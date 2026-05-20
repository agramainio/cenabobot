from __future__ import annotations

from html import escape

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.menu import (
    accepted_meal_keyboard,
    favorites_keyboard,
    main_menu_keyboard,
    recipe_keyboard,
    shopping_keyboard,
    suggestion_keyboard,
)
from app.db.models import MealProposal, MealVote, Recipe
from app.db.session import AsyncSessionLocal
from app.services.auth import (
    identity_text,
    is_authorized,
    reject_callback_if_unauthorized,
    reject_message_if_unauthorized,
)
from app.services.formatting import recipe_detail_text, shopping_list_text, suggestion_text
from app.services.recipes import (
    FILTER_LABELS,
    create_meal_proposal,
    ensure_actor,
    get_favorites,
    get_meal_proposal_details,
    get_one_suggestion,
    get_recipe,
    mark_meal_proposal_done,
    record_feedback,
    save_favorite,
    set_meal_proposal_message_id,
    set_meal_vote,
)

router = Router()


def _is_group_chat(message: Message) -> bool:
    return message.chat.type in {"group", "supergroup"}


def _display_name(callback: CallbackQuery) -> str:
    user = callback.from_user
    if user.first_name:
        return user.first_name
    if user.username:
        return f"@{user.username}"
    return str(user.id)


def _vote_status_text(votes: list[MealVote]) -> str:
    if not votes:
        return "Votes : aucun vote pour l’instant."

    labels = {
        "ok": "ok",
        "no": "pas ce soir",
    }

    parts = []
    for vote in votes:
        name = escape(vote.user_name or str(vote.user_id))
        value = labels.get(vote.vote, vote.vote)
        parts.append(f"{name} : {escape(value)}")

    return "Votes : " + " · ".join(parts)


def _proposal_text(
    recipe: Recipe,
    *,
    filter_label: str | None,
    votes: list[MealVote],
    proposal: MealProposal | None = None,
) -> str:
    base = suggestion_text(recipe, filter_label)
    status = _vote_status_text(votes)

    if proposal and proposal.status == "accepted":
        return f"{base}\n\n✅ <b>Repas validé</b>\n{status}"

    if proposal and proposal.status == "done":
        return f"{base}\n\n✅ <b>Repas marqué comme fait</b>\n{status}"

    return f"{base}\n\n{status}"


async def _ensure_actor_from_message(message: Message) -> None:
    if not message.from_user:
        return

    async with AsyncSessionLocal() as session:
        await ensure_actor(
            session,
            chat_id=message.chat.id,
            chat_title=message.chat.title,
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )


async def _ensure_actor_from_callback(callback: CallbackQuery) -> None:
    if not callback.message or not callback.from_user:
        return

    async with AsyncSessionLocal() as session:
        await ensure_actor(
            session,
            chat_id=callback.message.chat.id,
            chat_title=callback.message.chat.title,
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
        )


@router.message(Command("whoami"))
async def whoami(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else None
    chat_id = message.chat.id if message.chat else None

    await message.answer(
        "Identifiants Telegram pour cenabobot :\n\n"
        f"User ID : <code>{user_id}</code>\n"
        f"Chat ID : <code>{chat_id}</code>\n\n"
        "Pour autoriser cette conversation, ajoute ce Chat ID à ALLOWED_CHAT_IDS "
        "dans .env.production sur le VPS, puis redémarre le bot."
    )


@router.message(Command("group"))
@router.message(Command("setup"))
async def group_setup(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else None
    chat_id = message.chat.id if message.chat else None

    await message.answer(
        "Configuration du groupe cenabobot :\n\n"
        f"User ID : <code>{user_id}</code>\n"
        f"Chat ID : <code>{chat_id}</code>\n\n"
        "Sur le VPS :\n"
        "1. Ouvre <code>/opt/cenabobot/.env.production</code>\n"
        "2. Ajoute ce Chat ID à <code>ALLOWED_CHAT_IDS</code>\n"
        "3. Redémarre le bot :\n"
        "<code>docker compose -f docker-compose.prod.yml --env-file .env.production restart bot</code>"
    )


@router.message(Command("start"))
async def start(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else None
    chat_id = message.chat.id if message.chat else None

    if not is_authorized(user_id, chat_id):
        await message.answer(identity_text(user_id, chat_id))
        return

    await _ensure_actor_from_message(message)
    await message.answer(
        "cenabobot est prêt.\n\n"
        "Une idée de repas fiable à la fois.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    if await reject_message_if_unauthorized(message):
        return

    await message.answer(
        "cenabobot est privé.\n\n"
        "Utilise les boutons pour demander une idée, voir la recette, "
        "faire une liste de courses ou proposer une autre idée.\n\n"
        "En groupe, chacun peut répondre : Ça me va / Pas ce soir.\n\n"
        "V2 n’a toujours pas d’IA : seules les recettes enregistrées peuvent être proposées."
    )


@router.callback_query(F.data == "menu")
async def show_menu(callback: CallbackQuery) -> None:
    if await reject_callback_if_unauthorized(callback):
        return

    await _ensure_actor_from_callback(callback)
    await callback.answer()

    if callback.message:
        await callback.message.edit_text(
            "Que veux-tu faire ?",
            reply_markup=main_menu_keyboard(),
        )


@router.callback_query(F.data.startswith("suggest:"))
async def suggest(callback: CallbackQuery) -> None:
    if await reject_callback_if_unauthorized(callback):
        return

    await _ensure_actor_from_callback(callback)
    await callback.answer()

    filter_key = callback.data.split(":", 1)[1] if callback.data else "any"
    await _send_suggestion(callback, filter_key, force_new_group_message=True)


@router.callback_query(F.data.startswith("next:"))
async def next_idea(callback: CallbackQuery) -> None:
    if await reject_callback_if_unauthorized(callback):
        return

    await _ensure_actor_from_callback(callback)
    await callback.answer()

    filter_key = callback.data.split(":", 1)[1] if callback.data else "any"
    await _send_suggestion(callback, filter_key, force_new_group_message=True)


async def _send_suggestion(
    callback: CallbackQuery,
    filter_key: str,
    *,
    force_new_group_message: bool = False,
) -> None:
    if not callback.message:
        return

    filter_key = filter_key if filter_key in FILTER_LABELS else "any"
    is_group = _is_group_chat(callback.message)

    async with AsyncSessionLocal() as session:
        recipe = await get_one_suggestion(
            session,
            chat_id=callback.message.chat.id,
            user_id=callback.from_user.id if callback.from_user else None,
            filter_key=filter_key,
        )

        if recipe is None:
            if is_group:
                await callback.message.answer(
                    "Aucune recette enregistrée ne correspond encore.\n\n"
                    "Ajoute plus de recettes au catalogue, puis réessaie.",
                    reply_markup=main_menu_keyboard(),
                )
            else:
                await callback.message.edit_text(
                    "Aucune recette enregistrée ne correspond encore.\n\n"
                    "Ajoute plus de recettes au catalogue, puis réessaie.",
                    reply_markup=main_menu_keyboard(),
                )
            return

        proposal = None
        if is_group:
            proposal = await create_meal_proposal(
                session,
                chat_id=callback.message.chat.id,
                message_id=None,
                recipe_id=recipe.id,
                filter_key=filter_key,
                created_by_user_id=callback.from_user.id if callback.from_user else None,
            )

    if is_group and proposal is not None:
        text = _proposal_text(
            recipe,
            filter_label=FILTER_LABELS.get(filter_key),
            votes=[],
            proposal=proposal,
        )

        sent_message = await callback.message.answer(
            text,
            reply_markup=suggestion_keyboard(
                recipe.id,
                filter_key,
                recipe.servings,
                proposal_id=proposal.id,
            ),
        )

        async with AsyncSessionLocal() as session:
            await set_meal_proposal_message_id(
                session,
                proposal_id=proposal.id,
                message_id=sent_message.message_id,
            )
        return

    await callback.message.edit_text(
        suggestion_text(recipe, FILTER_LABELS.get(filter_key)),
        reply_markup=suggestion_keyboard(recipe.id, filter_key, recipe.servings),
    )


@router.callback_query(F.data.startswith("vote:"))
async def vote(callback: CallbackQuery) -> None:
    if await reject_callback_if_unauthorized(callback):
        return

    await _ensure_actor_from_callback(callback)

    if not callback.data or not callback.message or not callback.from_user:
        await callback.answer()
        return

    _, vote_value, proposal_id_text = callback.data.split(":", 2)

    if vote_value not in {"ok", "no"}:
        await callback.answer("Vote inconnu.", show_alert=False)
        return

    try:
        proposal_id = int(proposal_id_text)
    except ValueError:
        await callback.answer("Vote invalide.", show_alert=False)
        return

    async with AsyncSessionLocal() as session:
        proposal, recipe, votes = await set_meal_vote(
            session,
            proposal_id=proposal_id,
            user_id=callback.from_user.id,
            user_name=_display_name(callback),
            vote=vote_value,
        )

    if proposal is None or recipe is None:
        await callback.answer("Proposition introuvable.", show_alert=False)
        return

    if vote_value == "ok":
        await callback.answer("Noté : ça te va.", show_alert=False)
    else:
        await callback.answer("Noté : pas ce soir.", show_alert=False)

    filter_key = proposal.filter_key or "any"
    text = _proposal_text(
        recipe,
        filter_label=FILTER_LABELS.get(filter_key),
        votes=votes,
        proposal=proposal,
    )

    if proposal.status == "accepted":
        keyboard = accepted_meal_keyboard(proposal.id, recipe.id, filter_key, recipe.servings)
    else:
        keyboard = suggestion_keyboard(
            recipe.id,
            filter_key,
            recipe.servings,
            proposal_id=proposal.id,
        )

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("done:"))
async def mark_done(callback: CallbackQuery) -> None:
    if await reject_callback_if_unauthorized(callback):
        return

    await _ensure_actor_from_callback(callback)

    if not callback.data or not callback.message:
        await callback.answer()
        return

    _, proposal_id_text = callback.data.split(":", 1)

    try:
        proposal_id = int(proposal_id_text)
    except ValueError:
        await callback.answer("Proposition invalide.", show_alert=False)
        return

    async with AsyncSessionLocal() as session:
        proposal, recipe, votes = await mark_meal_proposal_done(
            session,
            proposal_id=proposal_id,
        )

        if proposal and recipe:
            await record_feedback(
                session,
                chat_id=proposal.chat_id,
                user_id=callback.from_user.id if callback.from_user else None,
                recipe_id=recipe.id,
                feedback_type="done",
                reason="meal_marked_done",
            )

    if proposal is None or recipe is None:
        await callback.answer("Proposition introuvable.", show_alert=False)
        return

    await callback.answer("Repas marqué comme fait.", show_alert=False)

    filter_key = proposal.filter_key or "any"
    await callback.message.edit_text(
        _proposal_text(
            recipe,
            filter_label=FILTER_LABELS.get(filter_key),
            votes=votes,
            proposal=proposal,
        ),
        reply_markup=accepted_meal_keyboard(proposal.id, recipe.id, filter_key, recipe.servings),
    )


@router.callback_query(F.data.startswith("recipe:"))
async def show_recipe(callback: CallbackQuery) -> None:
    if await reject_callback_if_unauthorized(callback):
        return

    await callback.answer()

    if not callback.data or not callback.message:
        return

    _, filter_key, recipe_id = callback.data.split(":", 2)

    async with AsyncSessionLocal() as session:
        recipe = await get_recipe(session, recipe_id)

    if recipe is None:
        await callback.message.edit_text("Recette introuvable.", reply_markup=main_menu_keyboard())
        return

    if _is_group_chat(callback.message):
        await callback.message.answer(
            recipe_detail_text(recipe),
            reply_markup=recipe_keyboard(recipe.id, filter_key, recipe.servings),
        )
        return

    await callback.message.edit_text(
        recipe_detail_text(recipe),
        reply_markup=recipe_keyboard(recipe.id, filter_key, recipe.servings),
    )


@router.callback_query(F.data.startswith("shop:"))
async def show_shopping_list(callback: CallbackQuery) -> None:
    if await reject_callback_if_unauthorized(callback):
        return

    await callback.answer()

    if not callback.data or not callback.message:
        return

    _, filter_key, recipe_id, servings_text = callback.data.split(":", 3)

    try:
        servings = int(servings_text)
    except ValueError:
        servings = 2

    async with AsyncSessionLocal() as session:
        recipe = await get_recipe(session, recipe_id)

    if recipe is None:
        await callback.message.edit_text("Recette introuvable.", reply_markup=main_menu_keyboard())
        return

    if _is_group_chat(callback.message):
        await callback.message.answer(
            shopping_list_text(recipe, target_servings=servings),
            reply_markup=shopping_keyboard(recipe.id, filter_key),
        )
        return

    await callback.message.edit_text(
        shopping_list_text(recipe, target_servings=servings),
        reply_markup=shopping_keyboard(recipe.id, filter_key),
    )


@router.callback_query(F.data.startswith("save:"))
async def save(callback: CallbackQuery) -> None:
    if await reject_callback_if_unauthorized(callback):
        return

    if not callback.data or not callback.message or not callback.from_user:
        await callback.answer()
        return

    _, recipe_id = callback.data.split(":", 1)

    async with AsyncSessionLocal() as session:
        created = await save_favorite(
            session,
            chat_id=callback.message.chat.id,
            user_id=callback.from_user.id,
            recipe_id=recipe_id,
        )

    if created:
        await callback.answer("Enregistré.", show_alert=False)
    else:
        await callback.answer("Déjà enregistré.", show_alert=False)


@router.callback_query(F.data.startswith("reject:"))
async def reject(callback: CallbackQuery) -> None:
    if await reject_callback_if_unauthorized(callback):
        return

    await callback.answer("Passé.", show_alert=False)

    if not callback.data or not callback.message:
        return

    _, filter_key, recipe_id = callback.data.split(":", 2)

    async with AsyncSessionLocal() as session:
        await record_feedback(
            session,
            chat_id=callback.message.chat.id,
            user_id=callback.from_user.id if callback.from_user else None,
            recipe_id=recipe_id,
            feedback_type="not_this",
            reason="not_this",
        )

    await _send_suggestion(callback, filter_key, force_new_group_message=True)


@router.callback_query(F.data == "favorites")
async def favorites(callback: CallbackQuery) -> None:
    if await reject_callback_if_unauthorized(callback):
        return

    await callback.answer()

    if not callback.message or not callback.from_user:
        return

    async with AsyncSessionLocal() as session:
        recipes = await get_favorites(
            session,
            chat_id=callback.message.chat.id,
            user_id=callback.from_user.id,
        )

    if not recipes:
        await callback.message.edit_text(
            "Aucun favori pour l’instant.",
            reply_markup=main_menu_keyboard(),
        )
        return

    lines = ["<b>Tes favoris</b>", ""]
    for index, recipe in enumerate(recipes, start=1):
        lines.append(f"{index}. {recipe.title}")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=favorites_keyboard([recipe.id for recipe in recipes]),
    )


@router.message()
async def fallback(message: Message) -> None:
    if await reject_message_if_unauthorized(message):
        return

    await message.answer(
        "Utilise les boutons pour l’instant.\n\n"
        "V2 n’a pas encore d’IA ni de compréhension en texte libre.",
        reply_markup=main_menu_keyboard(),
    )
