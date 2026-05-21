from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🍽️ Proposer un repas", callback_data="suggest:any")],
            [
                InlineKeyboardButton(text="🥬 Végétarien", callback_data="suggest:vegetarian"),
                InlineKeyboardButton(text="⚡ Rapide", callback_data="suggest:fast"),
            ],
            [
                InlineKeyboardButton(text="🚫 Sans viande", callback_data="suggest:no_meat"),
                InlineKeyboardButton(text="🥛 Sans lactose", callback_data="suggest:no_lactose"),
            ],
            [
                InlineKeyboardButton(text="⭐ Favoris", callback_data="favorites"),
                InlineKeyboardButton(text="📝 Ajouter une recette", callback_data="import:menu"),
            ],
            [
                InlineKeyboardButton(text="📚 En attente", callback_data="import:pending"),
                InlineKeyboardButton(text="⚙️ Aide", callback_data="help:menu"),
            ],
        ]
    )


def import_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔗 Depuis un lien", callback_data="import:url"),
                InlineKeyboardButton(text="📋 Depuis un texte", callback_data="import:text"),
            ],
            [InlineKeyboardButton(text="📚 Recettes en attente", callback_data="import:pending")],
            [InlineKeyboardButton(text="⬅️ Menu", callback_data="menu")],
        ]
    )


def suggestion_keyboard(
    recipe_id: str,
    filter_key: str,
    servings: int = 2,
    proposal_id: int | None = None,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    if proposal_id is not None:
        rows.append(
            [
                InlineKeyboardButton(text="✅ Ça me va", callback_data=f"vote:ok:{proposal_id}"),
                InlineKeyboardButton(text="🙅 Pas ce soir", callback_data=f"vote:no:{proposal_id}"),
            ]
        )

    rows.extend(
        [
            [
                InlineKeyboardButton(text="👀 Recette", callback_data=f"recipe:{filter_key}:{recipe_id}"),
                InlineKeyboardButton(text="🛒 Courses", callback_data=f"shop:{filter_key}:{recipe_id}:{servings}"),
            ],
            [
                InlineKeyboardButton(text="🔁 Autre idée", callback_data=f"next:{filter_key}"),
                InlineKeyboardButton(text="⭐ Garder", callback_data=f"save:{recipe_id}"),
            ],
        ]
    )

    if proposal_id is None:
        rows.append([InlineKeyboardButton(text="🙅 Pas ce repas", callback_data=f"reject:{filter_key}:{recipe_id}")])

    rows.append([InlineKeyboardButton(text="⬅️ Menu", callback_data="menu")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def accepted_meal_keyboard(
    proposal_id: int,
    recipe_id: str,
    filter_key: str,
    servings: int = 2,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👀 Recette", callback_data=f"recipe:{filter_key}:{recipe_id}"),
                InlineKeyboardButton(text="🛒 Liste finale", callback_data=f"shop:{filter_key}:{recipe_id}:{servings}"),
            ],
            [InlineKeyboardButton(text="✅ Marquer comme fait", callback_data=f"done:{proposal_id}")],
            [InlineKeyboardButton(text="🔁 Autre idée", callback_data=f"next:{filter_key}")],
            [InlineKeyboardButton(text="⬅️ Menu", callback_data="menu")],
        ]
    )


def recipe_keyboard(recipe_id: str, filter_key: str, servings: int = 2) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Courses", callback_data=f"shop:{filter_key}:{recipe_id}:{servings}")],
            [
                InlineKeyboardButton(text="⭐ Garder", callback_data=f"save:{recipe_id}"),
                InlineKeyboardButton(text="🔁 Autre idée", callback_data=f"next:{filter_key}"),
            ],
            [InlineKeyboardButton(text="⬅️ Menu", callback_data="menu")],
        ]
    )


def shopping_keyboard(recipe_id: str, filter_key: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👤 1", callback_data=f"shop:{filter_key}:{recipe_id}:1"),
                InlineKeyboardButton(text="👥 2", callback_data=f"shop:{filter_key}:{recipe_id}:2"),
                InlineKeyboardButton(text="👥 4", callback_data=f"shop:{filter_key}:{recipe_id}:4"),
            ],
            [
                InlineKeyboardButton(text="👀 Recette", callback_data=f"recipe:{filter_key}:{recipe_id}"),
                InlineKeyboardButton(text="🔁 Autre idée", callback_data=f"next:{filter_key}"),
            ],
            [InlineKeyboardButton(text="⬅️ Menu", callback_data="menu")],
        ]
    )


def favorites_keyboard(recipe_ids: list[str]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"👀 Ouvrir {index + 1}", callback_data=f"recipe:any:{recipe_id}")]
        for index, recipe_id in enumerate(recipe_ids)
    ]
    rows.append([InlineKeyboardButton(text="⬅️ Menu", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def import_drafts_keyboard(drafts: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"📝 {title}", callback_data=f"import:open:{draft_id}")]
        for draft_id, title in drafts
    ]

    rows.append([InlineKeyboardButton(text="📝 Ajouter une recette", callback_data="import:menu")])
    rows.append([InlineKeyboardButton(text="⬅️ Menu", callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def import_draft_keyboard(draft_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Approuver", callback_data=f"import:approve:{draft_id}"),
                InlineKeyboardButton(text="🗑️ Refuser", callback_data=f"import:reject:{draft_id}"),
            ],
            [InlineKeyboardButton(text="📚 Recettes en attente", callback_data="import:pending")],
            [InlineKeyboardButton(text="⬅️ Menu", callback_data="menu")],
        ]
    )

