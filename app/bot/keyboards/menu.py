from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍽 Meal idea", callback_data="suggest:any")],
            [
                InlineKeyboardButton(text="🥬 Vegetarian", callback_data="suggest:vegetarian"),
                InlineKeyboardButton(text="🚫 No lactose", callback_data="suggest:no_lactose"),
            ],
            [
                InlineKeyboardButton(text="🚫 No meat", callback_data="suggest:no_meat"),
                InlineKeyboardButton(text="⚡ Fast", callback_data="suggest:fast"),
            ],
            [InlineKeyboardButton(text="⭐ Favorites", callback_data="favorites")],
        ]
    )


def suggestion_keyboard(recipe_id: str, filter_key: str, servings: int = 2) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Show recipe", callback_data=f"recipe:{filter_key}:{recipe_id}"),
                InlineKeyboardButton(text="Shopping list", callback_data=f"shop:{filter_key}:{recipe_id}:{servings}"),
            ],
            [
                InlineKeyboardButton(text="Next idea", callback_data=f"next:{filter_key}"),
                InlineKeyboardButton(text="Save", callback_data=f"save:{recipe_id}"),
            ],
            [InlineKeyboardButton(text="Not this", callback_data=f"reject:{filter_key}:{recipe_id}")],
        ]
    )


def recipe_keyboard(recipe_id: str, filter_key: str, servings: int = 2) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Shopping list", callback_data=f"shop:{filter_key}:{recipe_id}:{servings}")],
            [
                InlineKeyboardButton(text="Save", callback_data=f"save:{recipe_id}"),
                InlineKeyboardButton(text="Next idea", callback_data=f"next:{filter_key}"),
            ],
            [InlineKeyboardButton(text="Main menu", callback_data="menu")],
        ]
    )


def shopping_keyboard(recipe_id: str, filter_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1 person", callback_data=f"shop:{filter_key}:{recipe_id}:1"),
                InlineKeyboardButton(text="2 people", callback_data=f"shop:{filter_key}:{recipe_id}:2"),
                InlineKeyboardButton(text="4 people", callback_data=f"shop:{filter_key}:{recipe_id}:4"),
            ],
            [
                InlineKeyboardButton(text="Recipe", callback_data=f"recipe:{filter_key}:{recipe_id}"),
                InlineKeyboardButton(text="Next idea", callback_data=f"next:{filter_key}"),
            ],
            [InlineKeyboardButton(text="Main menu", callback_data="menu")],
        ]
    )


def favorites_keyboard(recipe_ids: list[str]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"Open {index + 1}", callback_data=f"recipe:any:{recipe_id}")]
        for index, recipe_id in enumerate(recipe_ids)
    ]
    rows.append([InlineKeyboardButton(text="Main menu", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
