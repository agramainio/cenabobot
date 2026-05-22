from __future__ import annotations

from decimal import Decimal
from html import escape

from app.db.models import Recipe, RecipeIngredient, RecipeTag
from app.services.i18n import t


TAG_LABEL_KEYS = {
    "vegetarian": "tag.vegetarian",
    "vegan": "tag.vegan",
    "no_meat": "tag.no_meat",
    "no_fish": "tag.no_fish",
    "lactose_free": "tag.lactose_free",
    "dairy_free": "tag.dairy_free",
    "contains_egg": "tag.contains_egg",
    "contains_dairy": "tag.contains_dairy",
    "contains_fish": "tag.contains_fish",
    "contains_meat": "tag.contains_meat",
    "fast": "tag.fast",
    "cheap": "tag.cheap",
    "common_paris_ingredients": "tag.common_paris_ingredients",
}

PREFERRED_TAG_ORDER = [
    "vegetarian",
    "vegan",
    "lactose_free",
    "dairy_free",
    "no_meat",
    "no_fish",
    "fast",
    "cheap",
    "common_paris_ingredients",
    "contains_egg",
    "contains_dairy",
    "contains_fish",
    "contains_meat",
]


def total_minutes(recipe: Recipe) -> int | None:
    prep = recipe.prep_minutes or 0
    cook = recipe.cook_minutes or 0
    total = prep + cook
    return total if total > 0 else None


def tag_text(tags: list[RecipeTag]) -> str:
    tag_values = [tag.tag for tag in tags]
    ordered_values: list[str] = []

    for item in PREFERRED_TAG_ORDER:
        if item in tag_values and item not in ordered_values:
            ordered_values.append(item)

    for item in tag_values:
        if item not in ordered_values:
            ordered_values.append(item)

    labels = [
        t(TAG_LABEL_KEYS.get(item, "tag.unknown"), value=item.replace("_", " "))
        for item in ordered_values
    ]

    return " · ".join(labels[:6])


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
    time_text = f"{minutes} min" if minutes else t("recipe.unknown_time")
    tags = tag_text(recipe.tags)

    preference = escape(filter_label) if filter_label else t("filter.any")

    return (
        f"<b>{escape(recipe.title)}</b>\n\n"
        f"{escape(recipe.short_description or t('recipe.private_idea'))}\n\n"
        f"({escape(tags)} · {escape(time_text)})\n"
        f"{t('recipe.preference')} : {preference}"
    )


def recipe_detail_text(recipe: Recipe) -> str:
    minutes = total_minutes(recipe)
    time_text = f"{minutes} min" if minutes else t("recipe.unknown_time")
    tags = tag_text(recipe.tags)

    ingredients = "\n".join(
        ingredient_line(item)
        for item in sorted(recipe.ingredients, key=lambda x: x.display_order)
    )

    source = ""
    if recipe.source_name:
        source += f"\n\n{t('recipe.source')} : {escape(recipe.source_name)}"
    if recipe.source_url:
        source += f"\n{escape(recipe.source_url)}"

    return (
        f"<b>{escape(recipe.title)}</b>\n\n"
        f"{t('recipe.portions')} : {recipe.servings}\n"
        f"{t('recipe.time')} : {escape(time_text)}\n"
        f"{t('recipe.tags')} : {escape(tags)}\n\n"
        f"<b>{t('recipe.ingredients')}</b>\n"
        f"{ingredients or t('recipe.no_ingredients')}\n\n"
        f"<b>{t('recipe.summary')}</b>\n"
        f"{escape(recipe.short_description or t('recipe.no_summary'))}\n\n"
        f"<b>{t('recipe.preparation')}</b>\n"
        f"{escape(getattr(recipe, 'notes', None) or t('recipe.no_preparation'))}"
        f"{source}"
    )


def shopping_list_text(recipe: Recipe, target_servings: int | None = None) -> str:
    base_servings = recipe.servings or 2
    servings = target_servings or base_servings
    scale = servings / base_servings
    plural = "s" if servings > 1 else ""

    grouped: dict[str, list[RecipeIngredient]] = {}
    for ingredient in recipe.ingredients:
        category = ingredient.category or "autre"
        grouped.setdefault(category, []).append(ingredient)

    lines = [
        f"<b>{t('shopping.title', servings=servings, plural=plural)}</b>",
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
