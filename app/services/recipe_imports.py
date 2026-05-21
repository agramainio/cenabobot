from __future__ import annotations

from datetime import UTC, datetime
from textwrap import shorten

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RecipeImportDraft


def draft_display_title(draft: RecipeImportDraft) -> str:
    if draft.proposed_title:
        return draft.proposed_title

    if draft.source_url:
        return shorten(draft.source_url, width=52, placeholder="…")

    if draft.raw_text:
        return shorten(" ".join(draft.raw_text.split()), width=52, placeholder="…")

    return f"Brouillon #{draft.id}"


async def create_recipe_import_draft(
    session: AsyncSession,
    *,
    source_type: str,
    submitted_by_user_id: int,
    submitted_by_name: str | None,
    source_url: str | None = None,
    raw_text: str | None = None,
) -> RecipeImportDraft:
    draft = RecipeImportDraft(
        source_type=source_type,
        source_url=source_url,
        raw_text=raw_text,
        submitted_by_user_id=submitted_by_user_id,
        submitted_by_name=submitted_by_name,
        status="pending",
        proposed_title=None,
        proposed_recipe_id=None,
        proposed_yaml=None,
        warnings="Génération du brouillon non encore implémentée.",
        validation_errors="Le brouillon structuré n’existe pas encore.",
    )
    session.add(draft)
    await session.commit()
    await session.refresh(draft)
    return draft


async def get_recipe_import_draft(
    session: AsyncSession,
    draft_id: int,
) -> RecipeImportDraft | None:
    return await session.get(RecipeImportDraft, draft_id)


async def list_pending_recipe_import_drafts(
    session: AsyncSession,
    *,
    limit: int = 10,
) -> list[RecipeImportDraft]:
    result = await session.execute(
        select(RecipeImportDraft)
        .where(RecipeImportDraft.status == "pending")
        .order_by(RecipeImportDraft.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def reject_recipe_import_draft(
    session: AsyncSession,
    *,
    draft_id: int,
) -> RecipeImportDraft | None:
    draft = await session.get(RecipeImportDraft, draft_id)
    if draft is None:
        return None

    draft.status = "rejected"
    await session.commit()
    await session.refresh(draft)
    return draft


async def try_approve_recipe_import_draft_skeleton(
    session: AsyncSession,
    *,
    draft_id: int,
    approved_by_user_id: int,
) -> tuple[RecipeImportDraft | None, bool, str]:
    draft = await session.get(RecipeImportDraft, draft_id)
    if draft is None:
        return None, False, "Brouillon introuvable."

    if draft.status != "pending":
        return draft, False, "Ce brouillon n’est plus en attente."

    if not draft.proposed_yaml:
        return (
            draft,
            False,
            "Approbation bloquée : la génération YAML/AI n’est pas encore implémentée.",
        )

    if draft.validation_errors:
        return (
            draft,
            False,
            "Approbation bloquée : le brouillon contient encore des erreurs de validation.",
        )

    draft.status = "approved"
    draft.approved_by_user_id = approved_by_user_id
    draft.approved_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(draft)

    return draft, True, "Brouillon approuvé."
