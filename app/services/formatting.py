from __future__ import annotations

from decimal import Decimal
from html import escape

from app.db.models import Recipe, RecipeIngredient, RecipeTag

TAG_LABELS = {
    "vegetarian": "vegetarian",
    "no_meat": "no meat",
    "no_fish": "no fish",
    "lactose_free": "lactose-free",
    "dairy_free": "dairy-free",
    "contains_egg": "contains egg",
    "contains_dairy": "contains dairy",
    "contains_fish": "contains fish",
    "fast": "fast",
    "cheap": "cheap",
    "common_paris_ingredients": "common ingredients",
}


def total_minutes(recipe: Recipe) -> int | None:
    prep = recipe.prep_minutes or 0
    cook = recipe.cook_minutes or 0
    total = prep + cook
    return total if total > 0 else None


def tag_text(tags: list[RecipeTag]) -> str:
    labels = [TAG_LABELS.get(tag.tag, tag.tag.replace("_", " ")) for tag in tags]
    preferred_order = [
        "vegetarian",
        "lactose-free",
        "no meat",
        "fast",
        "cheap",
        "common ingredients",
    ]

    ordered: list[str] = []
    for item in preferred_order:
        if item in labels and item not in ordered:
            ordered.append(item)

    for item in labels:
        if item not in ordered:
            ordered.append(item)

    return " · ".join(ordered[:5])


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
    optional = " optional" if ingredient.optional else ""

    prefix = " ".join(part for part in [quantity_text, unit] if part).strip()

    if prefix:
        return f"- {prefix} {name}{optional}"

    return f"- {name}{optional}"


def suggestion_text(recipe: Recipe, filter_label: str | None = None) -> str:
    minutes = total_minutes(recipe)
    time_text = f"{minutes} min" if minutes else "time not set"
    tags = tag_text(recipe.tags)

    filter_line = f"\nPreference: {escape(filter_label)}" if filter_label else ""

    return (
        "Tonight's idea:\n\n"
        f"<b>{escape(recipe.title)}</b>\n\n"
        f"{escape(tags)} · {escape(time_text)}"
        f"{filter_line}\n\n"
        f"{escape(recipe.short_description or 'A simple meal from your private catalogue.')}"
    )


def recipe_detail_text(recipe: Recipe) -> str:
    minutes = total_minutes(recipe)
    time_text = f"{minutes} min" if minutes else "time not set"
    tags = tag_text(recipe.tags)

    ingredients = "\n".join(
        ingredient_line(item)
        for item in sorted(recipe.ingredients, key=lambda x: x.display_order)
    )

    source = ""
    if recipe.source_name:
        source += f"\n\nSource: {escape(recipe.source_name)}"
    if recipe.source_url:
        source += f"\n{escape(recipe.source_url)}"

    return (
        f"<b>{escape(recipe.title)}</b>\n\n"
        f"Servings: {recipe.servings}\n"
        f"Time: {escape(time_text)}\n"
        f"Tags: {escape(tags)}\n\n"
        f"<b>Ingredients</b>\n"
        f"{ingredients or '- No ingredients recorded'}\n\n"
        f"<b>Notes</b>\n"
        f"{escape(recipe.short_description or 'No notes yet.')}"
        f"{source}"
    )


def shopping_list_text(recipe: Recipe, target_servings: int | None = None) -> str:
    base_servings = recipe.servings or 2
    servings = target_servings or base_servings
    scale = servings / base_servings

    grouped: dict[str, list[RecipeIngredient]] = {}
    for ingredient in recipe.ingredients:
        category = ingredient.category or "other"
        grouped.setdefault(category, []).append(ingredient)

    lines = [
        f"<b>Shopping list for {servings} people</b>",
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
