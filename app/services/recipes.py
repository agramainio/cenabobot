from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Favorite,
    MealProposal,
    MealVote,
    Recipe,
    RecipeFeedback,
    RecipeIngredient,
    RecipeTag,
    SuggestionHistory,
    TelegramGroup,
    TelegramUser,
)

FILTER_TAGS = {
    "any": None,
    "vegetarian": "vegetarian",
    "no_lactose": "lactose_free",
    "no_meat": "no_meat",
    "fast": "fast",
}

FILTER_LABELS = {
    "any": "repas simple",
    "vegetarian": "végétarien",
    "no_lactose": "sans lactose",
    "no_meat": "sans viande",
    "fast": "rapide",
}


async def ensure_actor(
    session: AsyncSession,
    *,
    chat_id: int,
    chat_title: str | None,
    user_id: int,
    username: str | None,
    first_name: str | None,
) -> None:
    await session.merge(TelegramGroup(chat_id=chat_id, title=chat_title))
    await session.merge(
        TelegramUser(
            user_id=user_id,
            username=username,
            first_name=first_name,
        )
    )
    await session.commit()


def _recipe_query_with_relationships():
    return select(Recipe).options(
        selectinload(Recipe.tags),
        selectinload(Recipe.ingredients),
    )


async def get_recipe(session: AsyncSession, recipe_id: str) -> Recipe | None:
    result = await session.execute(
        _recipe_query_with_relationships().where(Recipe.id == recipe_id)
    )
    return result.scalar_one_or_none()


async def get_one_suggestion(
    session: AsyncSession,
    *,
    chat_id: int,
    user_id: int | None,
    filter_key: str = "any",
) -> Recipe | None:
    filter_key = filter_key if filter_key in FILTER_TAGS else "any"
    tag = FILTER_TAGS[filter_key]

    recent_result = await session.execute(
        select(SuggestionHistory.recipe_id)
        .where(SuggestionHistory.chat_id == chat_id)
        .order_by(SuggestionHistory.suggested_at.desc())
        .limit(8)
    )
    recent_recipe_ids = [row[0] for row in recent_result.all()]

    stmt = _recipe_query_with_relationships().where(Recipe.is_active.is_(True))

    if tag:
        stmt = stmt.join(RecipeTag).where(RecipeTag.tag == tag)

    if recent_recipe_ids:
        stmt = stmt.where(~Recipe.id.in_(recent_recipe_ids))

    stmt = stmt.order_by(func.random()).limit(1)

    result = await session.execute(stmt)
    recipe = result.scalar_one_or_none()

    if recipe is None and recent_recipe_ids:
        fallback_stmt = _recipe_query_with_relationships().where(Recipe.is_active.is_(True))

        if tag:
            fallback_stmt = fallback_stmt.join(RecipeTag).where(RecipeTag.tag == tag)

        fallback_stmt = fallback_stmt.order_by(func.random()).limit(1)
        fallback_result = await session.execute(fallback_stmt)
        recipe = fallback_result.scalar_one_or_none()

    if recipe is None:
        return None

    session.add(
        SuggestionHistory(
            chat_id=chat_id,
            user_id=user_id,
            recipe_id=recipe.id,
            filter_key=filter_key,
        )
    )
    await session.commit()

    return await get_recipe(session, recipe.id)


async def create_meal_proposal(
    session: AsyncSession,
    *,
    chat_id: int,
    message_id: int | None,
    recipe_id: str,
    filter_key: str,
    created_by_user_id: int | None,
) -> MealProposal:
    proposal = MealProposal(
        chat_id=chat_id,
        message_id=message_id,
        recipe_id=recipe_id,
        filter_key=filter_key,
        status="open",
        created_by_user_id=created_by_user_id,
    )
    session.add(proposal)
    await session.commit()
    await session.refresh(proposal)
    return proposal


async def set_meal_proposal_message_id(
    session: AsyncSession,
    *,
    proposal_id: int,
    message_id: int,
) -> None:
    proposal = await session.get(MealProposal, proposal_id)
    if proposal is None:
        return

    proposal.message_id = message_id
    await session.commit()


async def get_meal_proposal_details(
    session: AsyncSession,
    proposal_id: int,
) -> tuple[MealProposal | None, Recipe | None, list[MealVote]]:
    proposal = await session.get(MealProposal, proposal_id)
    if proposal is None:
        return None, None, []

    recipe = await get_recipe(session, proposal.recipe_id)

    result = await session.execute(
        select(MealVote)
        .where(MealVote.proposal_id == proposal_id)
        .order_by(MealVote.updated_at.asc())
    )
    votes = list(result.scalars().all())

    return proposal, recipe, votes


async def set_meal_vote(
    session: AsyncSession,
    *,
    proposal_id: int,
    user_id: int,
    user_name: str | None,
    vote: str,
) -> tuple[MealProposal | None, Recipe | None, list[MealVote]]:
    proposal = await session.get(MealProposal, proposal_id)
    if proposal is None:
        return None, None, []

    result = await session.execute(
        select(MealVote)
        .where(MealVote.proposal_id == proposal_id)
        .where(MealVote.user_id == user_id)
    )
    existing_vote = result.scalar_one_or_none()

    if existing_vote is None:
        session.add(
            MealVote(
                proposal_id=proposal_id,
                user_id=user_id,
                user_name=user_name,
                vote=vote,
                updated_at=datetime.now(UTC),
            )
        )
    else:
        existing_vote.vote = vote
        existing_vote.user_name = user_name
        existing_vote.updated_at = datetime.now(UTC)

    await session.flush()

    ok_result = await session.execute(
        select(func.count())
        .select_from(MealVote)
        .where(MealVote.proposal_id == proposal_id)
        .where(MealVote.vote == "ok")
    )
    ok_count = int(ok_result.scalar_one())

    if proposal.status == "open" and ok_count >= 2:
        proposal.status = "accepted"
        proposal.accepted_at = datetime.now(UTC)

    await session.commit()

    return await get_meal_proposal_details(session, proposal_id)


async def mark_meal_proposal_done(
    session: AsyncSession,
    *,
    proposal_id: int,
) -> tuple[MealProposal | None, Recipe | None, list[MealVote]]:
    proposal = await session.get(MealProposal, proposal_id)
    if proposal is None:
        return None, None, []

    proposal.status = "done"
    await session.commit()

    return await get_meal_proposal_details(session, proposal_id)


async def save_favorite(
    session: AsyncSession,
    *,
    chat_id: int,
    user_id: int,
    recipe_id: str,
) -> bool:
    session.add(Favorite(chat_id=chat_id, user_id=user_id, recipe_id=recipe_id))

    try:
        await session.commit()
        return True
    except IntegrityError:
        await session.rollback()
        return False


async def get_favorites(
    session: AsyncSession,
    *,
    chat_id: int,
    user_id: int,
) -> list[Recipe]:
    result = await session.execute(
        select(Recipe)
        .join(Favorite, Favorite.recipe_id == Recipe.id)
        .options(selectinload(Recipe.tags), selectinload(Recipe.ingredients))
        .where(Favorite.chat_id == chat_id)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
        .limit(10)
    )
    return list(result.scalars().all())


async def record_feedback(
    session: AsyncSession,
    *,
    chat_id: int,
    user_id: int | None,
    recipe_id: str,
    feedback_type: str,
    reason: str | None = None,
) -> None:
    session.add(
        RecipeFeedback(
            chat_id=chat_id,
            user_id=user_id,
            recipe_id=recipe_id,
            feedback_type=feedback_type,
            reason=reason,
        )
    )
    await session.commit()


async def replace_recipe_details(
    session: AsyncSession,
    *,
    recipe: Recipe,
    tags: list[str],
    ingredients: list[RecipeIngredient],
) -> None:
    existing = await session.get(Recipe, recipe.id)

    if existing is None:
        session.add(recipe)
    else:
        existing.title = recipe.title
        existing.short_description = recipe.short_description
        existing.notes = recipe.notes
        existing.source_name = recipe.source_name
        existing.source_url = recipe.source_url
        existing.servings = recipe.servings
        existing.prep_minutes = recipe.prep_minutes
        existing.cook_minutes = recipe.cook_minutes
        existing.is_active = recipe.is_active

    await session.flush()

    await session.execute(delete(RecipeTag).where(RecipeTag.recipe_id == recipe.id))
    await session.execute(delete(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe.id))

    for tag in sorted(set(tags)):
        session.add(RecipeTag(recipe_id=recipe.id, tag=tag))

    for item in ingredients:
        item.recipe_id = recipe.id
        session.add(item)

    await session.commit()
