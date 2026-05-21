from __future__ import annotations

from decimal import Decimal
from html import escape

from app.db.models import Recipe, RecipeIngredient, RecipeTag

TAG_LABELS = {
    "vegetarian": "végétarien",
    "no_meat": "sans viande",
    "no_fish": "sans poisson",
    "lactose_free": "sans lactose",
    "dairy_free": "sans produits laitiers",
    "contains_egg": "contient œuf",
    "contains_dairy": "contient produits laitiers",
    "contains_fish": "contient poisson",
    "fast": "rapide",
    "cheap": "économique",
    "common_paris_ingredients": "ingrédients courants",
}


def total_minutes(recipe: Recipe) -> int | None:
    prep = recipe.prep_minutes or 0
    cook = recipe.cook_minutes or 0
    total = prep + cook
    return total if total > 0 else None


def tag_text(tags: list[RecipeTag]) -> str:
    labels = [TAG_LABELS.get(tag.tag, tag.tag.replace("_", " ")) for tag in tags]

    preferred_order = [
        "végétarien",
        "sans lactose",
        "sans viande",
        "rapide",
        "économique",
        "ingrédients courants",
    ]

    ordered: list[str] = []
    for item in preferred_order:
        if item in labels and item not in ordered:
            ordered.append(item)

    for item in labels:
        if item not in ordered:
            ordered.append(item)

    return " · ".join(ordered[:6])


def format_quantity(value: object) -> str:
    if value is None:
        return ""

    if isinstance(value, Decimal):
        if value == value.to_integral_value():
            return str(int(value))
        return str(value.normalize())

    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    return str(value)


def ingredient_line(ingredient: RecipeIngredient, scale: float = 1.0) -> str:
    quantity = ingredient.quantity
    quantity_text = ""

    if quantity is not None:
        scaled = Decimal(str(quantity)) * Decimal(str(scale))
        quantity_text = format_quantity(scaled)

    unit = ingredient.unit or ""
    name = escape(ingredient.name)
    optional = " facultatif" if ingredient.optional else ""

    prefix = " ".join(part for part in [quantity_text, unit] if part).strip()

    if prefix:
        return f"- {prefix} {name}{optional}"

    return f"- {name}{optional}"


def suggestion_text(recipe: Recipe, filter_label: str | None = None) -> str:
    minutes = total_minutes(recipe)
    time_text = f"{minutes} min" if minutes else "temps non renseigné"
    tags = tag_text(recipe.tags)

    preference = escape(filter_label) if filter_label else "repas simple"

    return (
        f"<b>{escape(recipe.title)}</b>\n\n"
        f"{escape(recipe.short_description or 'Une idée simple depuis ton catalogue privé.')}\n\n"
        f"({escape(tags)} · {escape(time_text)})\n"
        f"Préférence : {preference}"
    )


def recipe_detail_text(recipe: Recipe) -> str:
    minutes = total_minutes(recipe)
    time_text = f"{minutes} min" if minutes else "temps non renseigné"
    tags = tag_text(recipe.tags)

    ingredients = "\n".join(
        ingredient_line(item)
        for item in sorted(recipe.ingredients, key=lambda x: x.display_order)
    )

    source = ""
    if recipe.source_name:
        source += f"\n\nSource : {escape(recipe.source_name)}"
    if recipe.source_url:
        source += f"\n{escape(recipe.source_url)}"

    return (
        f"<b>{escape(recipe.title)}</b>\n\n"
        f"Portions : {recipe.servings}\n"
        f"Temps : {escape(time_text)}\n"
        f"Tags : {escape(tags)}\n\n"
        f"<b>Ingrédients</b>\n"
        f"{ingredients or '- Aucun ingrédient renseigné'}\n\n"
        f"<b>Résumé</b>\n"
        f"{escape(recipe.short_description or 'Pas encore de résumé.')}\n\n"
        f"<b>Préparation</b>\n"
        f"{escape(getattr(recipe, 'notes', None) or 'Pas encore de préparation détaillée.')}"
        f"{source}"
    )


def shopping_list_text(recipe: Recipe, target_servings: int | None = None) -> str:
    base_servings = recipe.servings or 2
    servings = target_servings or base_servings
    scale = servings / base_servings

    grouped: dict[str, list[RecipeIngredient]] = {}
    for ingredient in recipe.ingredients:
        category = ingredient.category or "autre"
        grouped.setdefault(category, []).append(ingredient)

    lines = [
        f"<b>Liste de courses pour {servings} personne{'s' if servings > 1 else ''}</b>",
        "",
        escape(recipe.title),
        "",
    ]

    for category in sorted(grouped):
        lines.append(f"<b>{escape(category.title())}</b>")
        for ingredient in sorted(grouped[category], key=lambda x: x.display_order):
            lines.append(ingredient_line(ingredient, scale=scale))
        lines.append("")

    return "\n".join(lines).strip()
