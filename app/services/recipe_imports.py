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
from app.services.recipes import replace_recipe_details


DAIRY_KEYWORDS = {
    "lait",
    "crème",
    "creme",
    "beurre",
    "fromage",
    "yaourt",
    "yogourt",
    "feta",
    "mozzarella",
    "parmesan",
    "ricotta",
    "chèvre",
    "chevre",
    "emmental",
    "comté",
    "comte",
    "gruyère",
    "gruyere",
}

EGG_KEYWORDS = {"œuf", "oeuf", "œufs", "oeufs", "egg", "eggs"}

FISH_KEYWORDS = {
    "thon",
    "saumon",
    "sardine",
    "maquereau",
    "cabillaud",
    "poisson",
    "crevette",
    "crevettes",
    "anchois",
    "truite",
    "colin",
    "merlu",
}

MEAT_KEYWORDS = {
    "poulet",
    "jambon",
    "lard",
    "boeuf",
    "bœuf",
    "porc",
    "saucisse",
    "chorizo",
    "dinde",
    "veau",
    "agneau",
    "canard",
    "bacon",
}

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


def _clean_line(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^[-*•]\s*", "", value)
    value = re.sub(r"^\d+[.)]\s*", "", value)
    return value.strip()


def _normalize_text(value: str) -> str:
    return _strip_accents(value.lower())


def _contains_any(value: str, keywords: set[str]) -> bool:
    normalized = _normalize_text(value)
    return any(_normalize_text(keyword) in normalized for keyword in keywords)


def _extract_minutes(raw_text: str) -> tuple[int | None, list[str]]:
    warnings: list[str] = []
    text = raw_text.lower()

    explicit = re.search(r"(\d{1,3})\s*(?:min|minutes)", text)
    if explicit:
        return int(explicit.group(1)), warnings

    hours = re.search(r"(\d{1,2})\s*(?:h|heure|heures)", text)
    if hours:
        return int(hours.group(1)) * 60, warnings

    warnings.append("Temps non trouvé : prep_minutes/cook_minutes estimés.")
    return None, warnings


def _extract_servings(raw_text: str) -> tuple[int, list[str]]:
    text = raw_text.lower()
    match = re.search(r"(\d{1,2})\s*(?:personnes|personne|portions|portion)", text)
    if match:
        return int(match.group(1)), []

    return 2, ["Portions non trouvées : 2 personnes par défaut."]


def _line_looks_like_ingredient(line: str) -> bool:
    lowered = line.lower()

    if not line:
        return False

    if lowered.rstrip(":") in {
        "ingrédients",
        "ingredients",
        "préparation",
        "preparation",
        "étapes",
        "etapes",
        "instructions",
        "recette",
    }:
        return False

    if re.match(r"^[-*•]\s+", line.strip()):
        return True

    if re.match(r"^\d+([,.]\d+)?\s*(g|kg|ml|cl|l|c\.|cuillère|cuilleres|càs|cas|pièce|pieces|gousse|gousses)?\b", lowered):
        return True

    if "," in line and len(line) < 160:
        return True

    return False


def _extract_ingredient_lines(lines: list[str]) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    ingredients: list[str] = []
    in_ingredients = False

    for raw_line in lines:
        lowered = raw_line.strip().lower().rstrip(":")

        if lowered in {"ingrédients", "ingredients"}:
            in_ingredients = True
            continue

        if lowered in {"préparation", "preparation", "étapes", "etapes", "instructions", "recette"}:
            in_ingredients = False
            continue

        if in_ingredients or _line_looks_like_ingredient(raw_line):
            cleaned = _clean_line(raw_line)
            if not cleaned:
                continue

            # A comma-separated single-line ingredient list is common in pasted notes.
            if "," in cleaned and not re.match(r"^\d", cleaned):
                ingredients.extend(_clean_line(part) for part in cleaned.split(",") if _clean_line(part))
            else:
                ingredients.append(cleaned)

    unique: list[str] = []
    seen: set[str] = set()
    for item in ingredients:
        normalized = item.lower()
        if normalized not in seen:
            unique.append(item)
            seen.add(normalized)

    if not unique:
        warnings.append("Aucun ingrédient clair trouvé.")

    return unique, warnings


def _parse_ingredient(raw: str, index: int) -> dict[str, Any]:
    cleaned = _clean_line(raw)
    quantity: float | None = None
    unit: str | None = None
    name = cleaned

    match = re.match(
        r"^(?P<quantity>\d+(?:[,.]\d+)?)\s*"
        r"(?P<unit>kg|g|mg|l|cl|ml|c\. à soupe|c\. à café|càs|cas|cuillère|cuillere|pièce|pieces|gousse|gousses)?\s+"
        r"(?P<name>.+)$",
        cleaned,
        flags=re.IGNORECASE,
    )

    if match:
        try:
            quantity = float(match.group("quantity").replace(",", "."))
        except ValueError:
            quantity = None

        unit = match.group("unit")
        name = match.group("name").strip()

    return {
        "name": name,
        "quantity": quantity,
        "unit": unit,
        "category": _guess_category(name),
        "optional": False,
        "display_order": index,
    }


def _guess_category(name: str) -> str:
    if _contains_any(name, MEAT_KEYWORDS):
        return "viande"

    if _contains_any(name, FISH_KEYWORDS):
        return "poisson"

    if _contains_any(name, DAIRY_KEYWORDS):
        return "produits laitiers"

    if _contains_any(name, EGG_KEYWORDS):
        return "œufs"

    if _contains_any(name, {"riz", "pâtes", "pates", "semoule", "boulgour", "quinoa", "lentilles", "pois chiches", "haricots"}):
        return "épicerie"

    if _contains_any(name, {"huile", "sel", "poivre", "cumin", "paprika", "sauce soja", "vinaigre"}):
        return "placard"

    return "légumes"


async def _unique_recipe_id(session: AsyncSession, title: str) -> str:
    base = _slugify(title)
    candidate = base
    suffix = 2

    while await session.get(Recipe, candidate) is not None:
        candidate = f"{base}_{suffix}"
        suffix += 1

    return candidate


def _infer_tags(ingredient_names: list[str], total_minutes: int | None) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    joined = " ".join(ingredient_names)

    has_meat = _contains_any(joined, MEAT_KEYWORDS)
    has_fish = _contains_any(joined, FISH_KEYWORDS)
    has_egg = _contains_any(joined, EGG_KEYWORDS)
    has_dairy = _contains_any(joined, DAIRY_KEYWORDS)

    tags: list[str] = ["common_paris_ingredients"]

    if has_meat:
        tags.append("contains_meat")
    else:
        tags.append("no_meat")

    if has_fish:
        tags.append("contains_fish")
    else:
        tags.append("no_fish")

    if has_egg:
        tags.append("contains_egg")

    if has_dairy:
        tags.append("contains_dairy")
        warnings.append("Produit laitier détecté : vérifier lactose_free / dairy_free.")
    else:
        tags.extend(["lactose_free", "dairy_free"])

    if not has_meat and not has_fish:
        tags.append("vegetarian")

    if not has_meat and not has_fish and not has_egg and not has_dairy:
        tags.append("vegan")

    if total_minutes is not None and total_minutes <= 30:
        tags.append("fast")

    return sorted(set(tags)), warnings


def _title_from_text(raw_text: str) -> str:
    for raw_line in raw_text.splitlines():
        line = _clean_line(raw_line)
        if not line:
            continue

        lowered = line.lower()
        if lowered.startswith(("titre:", "title:")):
            return line.split(":", 1)[1].strip() or "Recette importée"

        if lowered.rstrip(":") not in {"ingrédients", "ingredients", "préparation", "preparation"}:
            return shorten(line, width=80, placeholder="…")

    return "Recette importée"


async def generate_recipe_yaml_from_text(
    session: AsyncSession,
    raw_text: str,
) -> tuple[str | None, str | None, str | None, list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []

    normalized_raw = raw_text.strip()
    if not normalized_raw:
        return None, None, None, [], ["Texte vide."]

    title = _title_from_text(normalized_raw)
    recipe_id = await _unique_recipe_id(session, title)

    lines = [line for line in normalized_raw.splitlines() if line.strip()]
    ingredient_lines, ingredient_warnings = _extract_ingredient_lines(lines)
    warnings.extend(ingredient_warnings)

    ingredients = [
        _parse_ingredient(line, index)
        for index, line in enumerate(ingredient_lines)
    ]

    if not ingredients:
        errors.append("Impossible d’approuver : aucun ingrédient détecté.")

    servings, serving_warnings = _extract_servings(normalized_raw)
    warnings.extend(serving_warnings)

    total_minutes, minute_warnings = _extract_minutes(normalized_raw)
    warnings.extend(minute_warnings)

    if total_minutes is None:
        prep_minutes = 10
        cook_minutes = 20
    else:
        prep_minutes = min(10, total_minutes)
        cook_minutes = max(0, total_minutes - prep_minutes)

    tags, tag_warnings = _infer_tags([item["name"] for item in ingredients], total_minutes)
    warnings.extend(tag_warnings)

    short_description = f"Recette ajoutée depuis un texte par un utilisateur autorisé."

    data = {
        "id": recipe_id,
        "title": title,
        "short_description": short_description,
        "source_name": "import texte",
        "source_url": "",
        "servings": servings,
        "prep_minutes": prep_minutes,
        "cook_minutes": cook_minutes,
        "tags": tags,
        "ingredients": ingredients,
        "notes": normalized_raw,
        "concerns_or_tag_ambiguity": " ".join(warnings) if warnings else "",
    }

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

        if not str(ingredient.get("name") or "").strip():
            errors.append(f"ingredient #{index} sans nom.")

        optional = ingredient.get("optional", False)
        if not isinstance(optional, bool):
            errors.append(f"ingredient #{index} optional doit être true/false.")

        quantity = ingredient.get("quantity")
        if quantity is not None and not isinstance(quantity, (int, float)):
            warnings.append(f"ingredient #{index} quantity non numérique.")

    return errors, warnings


def _warnings_text(warnings: list[str]) -> str | None:
    if not warnings:
        return None

    return "\n".join(f"- {item}" for item in warnings)


def _errors_text(errors: list[str]) -> str | None:
    if not errors:
        return None

    return "\n".join(f"- {item}" for item in errors)


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
