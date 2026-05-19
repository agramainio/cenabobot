from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍽 Idée repas", callback_data="suggest:any")],
            [
                InlineKeyboardButton(text="🥬 Végétarien", callback_data="suggest:vegetarian"),
                InlineKeyboardButton(text="🚫 Sans lactose", callback_data="suggest:no_lactose"),
            ],
            [
                InlineKeyboardButton(text="🚫 Sans viande", callback_data="suggest:no_meat"),
                InlineKeyboardButton(text="⚡ Rapide", callback_data="suggest:fast"),
            ],
            [InlineKeyboardButton(text="⭐ Favoris", callback_data="favorites")],
        ]
    )


def suggestion_keyboard(recipe_id: str, filter_key: str, servings: int = 2) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Voir la recette", callback_data=f"recipe:{filter_key}:{recipe_id}"),
                InlineKeyboardButton(text="Liste de courses", callback_data=f"shop:{filter_key}:{recipe_id}:{servings}"),
            ],
            [
                InlineKeyboardButton(text="Idée suivante", callback_data=f"next:{filter_key}"),
                InlineKeyboardButton(text="Enregistrer", callback_data=f"save:{recipe_id}"),
            ],
            [InlineKeyboardButton(text="Pas ça", callback_data=f"reject:{filter_key}:{recipe_id}")],
        ]
    )


def recipe_keyboard(recipe_id: str, filter_key: str, servings: int = 2) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Liste de courses", callback_data=f"shop:{filter_key}:{recipe_id}:{servings}")],
            [
                InlineKeyboardButton(text="Enregistrer", callback_data=f"save:{recipe_id}"),
                InlineKeyboardButton(text="Idée suivante", callback_data=f"next:{filter_key}"),
            ],
            [InlineKeyboardButton(text="Menu", callback_data="menu")],
        ]
    )


def shopping_keyboard(recipe_id: str, filter_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1 personne", callback_data=f"shop:{filter_key}:{recipe_id}:1"),
                InlineKeyboardButton(text="2 personnes", callback_data=f"shop:{filter_key}:{recipe_id}:2"),
                InlineKeyboardButton(text="4 personnes", callback_data=f"shop:{filter_key}:{recipe_id}:4"),
            ],
            [
                InlineKeyboardButton(text="Recette", callback_data=f"recipe:{filter_key}:{recipe_id}"),
                InlineKeyboardButton(text="Idée suivante", callback_data=f"next:{filter_key}"),
            ],
            [InlineKeyboardButton(text="Menu", callback_data="menu")],
        ]
    )


def favorites_keyboard(recipe_ids: list[str]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"Ouvrir {index + 1}", callback_data=f"recipe:any:{recipe_id}")]
        for index, recipe_id in enumerate(recipe_ids)
    ]
    rows.append([InlineKeyboardButton(text="Menu", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
