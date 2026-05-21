from __future__ import annotations

import re
import unicodedata
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from textwrap import shorten
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Recipe, RecipeImportDraft, RecipeIngredient
from app.services.openai_recipe_drafts import (
    OpenAIRecipeDraftError,
    generate_recipe_draft_data,
)
from app.services.recipes import replace_recipe_details


KNOWN_TAGS = {
    "vegetarian",
    "vegan",
    "no_meat",
    "no_fish",
    "lactose_free",
    "dairy_free",
    "contains_egg",
    "contains_dairy",
    "contains_fish",
    "contains_meat",
    "fast",
    "cheap",
    "common_paris_ingredients",
}


def draft_display_title(draft: RecipeImportDraft) -> str:
    if draft.proposed_title:
        return draft.proposed_title

    if draft.source_url:
        return shorten(draft.source_url, width=52, placeholder="…")

    if draft.raw_text:
        return shorten(" ".join(draft.raw_text.split()), width=52, placeholder="…")

    return f"Brouillon #{draft.id}"


def _strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def _slugify(value: str) -> str:
    value = _strip_accents(value.lower())
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "recette_importee"


async def _unique_recipe_id(session: AsyncSession, title: str) -> str:
    base = _slugify(title)
    candidate = base
    suffix = 2

    while await session.get(Recipe, candidate) is not None:
        candidate = f"{base}_{suffix}"
        suffix += 1

    return candidate


def _warnings_text(warnings: list[str]) -> str | None:
    clean = [item.strip() for item in warnings if item and item.strip()]
    if not clean:
        return None

    return "\n".join(f"- {item}" for item in sorted(set(clean)))


def _errors_text(errors: list[str]) -> str | None:
    clean = [item.strip() for item in errors if item and item.strip()]
    if not clean:
        return None

    return "\n".join(f"- {item}" for item in sorted(set(clean)))


async def generate_recipe_yaml_from_text(
    session: AsyncSession,
    raw_text: str,
) -> tuple[str | None, str | None, str | None, list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []

    normalized_raw = raw_text.strip()
    if not normalized_raw:
        return None, None, None, [], ["Texte vide."]

    try:
        data = await generate_recipe_draft_data(normalized_raw)
    except OpenAIRecipeDraftError as exc:
        return None, None, None, [], [str(exc)]

    title = str(data.get("title") or "").strip()
    if not title:
        title = "Recette importée"
        warnings.append("Titre manquant : titre par défaut utilisé.")

    recipe_id = await _unique_recipe_id(session, title)

    ingredients = data.get("ingredients")
    if isinstance(ingredients, list):
        for index, ingredient in enumerate(ingredients):
            if isinstance(ingredient, dict):
                ingredient["display_order"] = index

    data["id"] = recipe_id
    data["title"] = title
    data["source_name"] = "import texte"
    data["source_url"] = ""

    ai_warnings = data.get("warnings")
    if isinstance(ai_warnings, list):
        warnings.extend(str(item) for item in ai_warnings if str(item).strip())

    data["concerns_or_tag_ambiguity"] = " ".join(warnings)

    validation_errors, validation_warnings = await validate_recipe_draft_data(session, data)
    errors.extend(validation_errors)
    warnings.extend(validation_warnings)

    proposed_yaml = yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        width=88,
    )

    return recipe_id, title, proposed_yaml, sorted(set(warnings)), sorted(set(errors))


async def validate_recipe_draft_data(
    session: AsyncSession,
    data: dict[str, Any],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    recipe_id = str(data.get("id") or "").strip()
    if not recipe_id:
        errors.append("id manquant.")
    elif not re.match(r"^[a-z0-9_]+$", recipe_id):
        errors.append("id invalide : utiliser minuscules, chiffres et underscores.")
    elif await session.get(Recipe, recipe_id) is not None:
        errors.append(f"id déjà utilisé : {recipe_id}")

    if not str(data.get("title") or "").strip():
        errors.append("title manquant.")

    if not str(data.get("short_description") or "").strip():
        warnings.append("short_description manquant.")

    servings = data.get("servings")
    if not isinstance(servings, int) or servings <= 0:
        errors.append("servings doit être un entier positif.")

    for key in ("prep_minutes", "cook_minutes"):
        value = data.get(key)
        if value is not None and (not isinstance(value, int) or value < 0):
            errors.append(f"{key} doit être un entier positif ou nul.")

    tags = data.get("tags")
    if not isinstance(tags, list) or not tags:
        errors.append("tags doit être une liste non vide.")
        tags = []

    for tag in tags:
        if tag not in KNOWN_TAGS:
            warnings.append(f"tag inconnu : {tag}")

    tag_set = set(tags)
    contradictions = [
        ("vegan", "contains_egg"),
        ("vegan", "contains_dairy"),
        ("vegan", "contains_fish"),
        ("vegan", "contains_meat"),
        ("vegetarian", "contains_fish"),
        ("vegetarian", "contains_meat"),
        ("dairy_free", "contains_dairy"),
        ("no_fish", "contains_fish"),
        ("no_meat", "contains_meat"),
    ]

    for left, right in contradictions:
        if left in tag_set and right in tag_set:
            errors.append(f"tags contradictoires : {left} + {right}")

    ingredients = data.get("ingredients")
    if not isinstance(ingredients, list) or not ingredients:
        errors.append("ingredients doit être une liste non vide.")
        return errors, warnings

    for index, ingredient in enumerate(ingredients, start=1):
        if not isinstance(ingredient, dict):
            errors.append(f"ingredient #{index} doit être un objet.")
            continue

        name = str(ingredient.get("name") or "").strip()
        if not name:
            errors.append(f"ingredient #{index} sans nom.")

        lowered = name.lower().strip()
        if re.match(r"^\d+\s*(personnes?|portions?)$", lowered):
            errors.append(f"ingredient #{index} est une métadonnée, pas un ingrédient : {name}")

        if re.match(r"^\d+\s*(min|minutes?)$", lowered):
            errors.append(f"ingredient #{index} est une durée, pas un ingrédient : {name}")

        optional = ingredient.get("optional", False)
        if not isinstance(optional, bool):
            errors.append(f"ingredient #{index} optional doit être true/false.")

        quantity = ingredient.get("quantity")
        if quantity is not None and not isinstance(quantity, (int, float)):
            warnings.append(f"ingredient #{index} quantity non numérique.")

    return errors, warnings


async def create_recipe_import_draft(
    session: AsyncSession,
    *,
    source_type: str,
    submitted_by_user_id: int,
    submitted_by_name: str | None,
    source_url: str | None = None,
    raw_text: str | None = None,
) -> RecipeImportDraft:
    proposed_recipe_id = None
    proposed_title = None
    proposed_yaml = None
    warnings: list[str] = []
    errors: list[str] = []

    if source_type == "text" and raw_text:
        (
            proposed_recipe_id,
            proposed_title,
            proposed_yaml,
            warnings,
            errors,
        ) = await generate_recipe_yaml_from_text(session, raw_text)
    elif source_type == "url":
        warnings.append("Import URL enregistré, mais lecture automatique du lien non encore implémentée.")
        errors.append("Le brouillon structuré n’existe pas encore pour les URL.")
    else:
        errors.append("Source de brouillon invalide ou vide.")

    draft = RecipeImportDraft(
        source_type=source_type,
        source_url=source_url,
        raw_text=raw_text,
        submitted_by_user_id=submitted_by_user_id,
        submitted_by_name=submitted_by_name,
        status="pending",
        proposed_title=proposed_title,
        proposed_recipe_id=proposed_recipe_id,
        proposed_yaml=proposed_yaml,
        warnings=_warnings_text(warnings),
        validation_errors=_errors_text(errors),
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


def _decimal_or_none(value: Any) -> Decimal | None:
    if value is None:
        return None

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _recipe_objects_from_yaml(proposed_yaml: str) -> tuple[Recipe, list[str], list[RecipeIngredient]]:
    data = yaml.safe_load(proposed_yaml)

    if not isinstance(data, dict):
        raise ValueError("YAML invalide.")

    recipe_id = str(data["id"]).strip()

    recipe = Recipe(
        id=recipe_id,
        title=str(data["title"]).strip(),
        short_description=str(data.get("short_description") or data.get("notes") or ""),
        source_name=data.get("source_name"),
        source_url=data.get("source_url"),
        servings=int(data.get("servings") or 2),
        prep_minutes=data.get("prep_minutes"),
        cook_minutes=data.get("cook_minutes"),
        is_active=True,
    )

    tags = [str(tag).strip() for tag in data.get("tags", []) if str(tag).strip()]

    ingredients: list[RecipeIngredient] = []
    for index, raw in enumerate(data.get("ingredients", [])):
        if not isinstance(raw, dict):
            continue

        ingredients.append(
            RecipeIngredient(
                recipe_id=recipe_id,
                name=str(raw.get("name") or "").strip(),
                quantity=_decimal_or_none(raw.get("quantity")),
                unit=raw.get("unit"),
                category=raw.get("category"),
                optional=bool(raw.get("optional", False)),
                display_order=int(raw.get("display_order", index)),
            )
        )

    return recipe, tags, ingredients


async def approve_recipe_import_draft(
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
        return draft, False, "Approbation bloquée : aucun YAML proposé."

    data = yaml.safe_load(draft.proposed_yaml)
    if not isinstance(data, dict):
        return draft, False, "Approbation bloquée : YAML invalide."

    errors, warnings = await validate_recipe_draft_data(session, data)
    draft.validation_errors = _errors_text(errors)
    draft.warnings = _warnings_text(warnings)

    if errors:
        await session.commit()
        await session.refresh(draft)
        return draft, False, "Approbation bloquée : erreurs de validation."

    recipe, tags, ingredients = _recipe_objects_from_yaml(draft.proposed_yaml)
    await replace_recipe_details(
        session,
        recipe=recipe,
        tags=tags,
        ingredients=ingredients,
    )

    draft.status = "approved"
    draft.approved_by_user_id = approved_by_user_id
    draft.approved_at = datetime.now(UTC)
    draft.validation_errors = None
    await session.commit()
    await session.refresh(draft)

    return draft, True, "Recette ajoutée au catalogue."
