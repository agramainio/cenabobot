from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.services.i18n import current_language, t


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("main.suggest"), callback_data="suggest:any")],
            [
                InlineKeyboardButton(text=t("main.vegetarian"), callback_data="suggest:vegetarian"),
                InlineKeyboardButton(text=t("main.fast"), callback_data="suggest:fast"),
            ],
            [
                InlineKeyboardButton(text=t("main.no_meat"), callback_data="suggest:no_meat"),
                InlineKeyboardButton(text=t("main.no_lactose"), callback_data="suggest:no_lactose"),
            ],
            [
                InlineKeyboardButton(text=t("main.favorites"), callback_data="favorites"),
                InlineKeyboardButton(text=t("main.add_recipe"), callback_data="import:menu"),
            ],
            [
                InlineKeyboardButton(text=t("main.pending"), callback_data="import:pending"),
                InlineKeyboardButton(text=t("main.settings"), callback_data="settings:menu"),
            ],
        ]
    )


def settings_keyboard() -> InlineKeyboardMarkup:
    language_label = "Français" if current_language() == "fr" else "Italiano"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{t('settings.language')} : {language_label}", callback_data="settings:language")],
            [
                InlineKeyboardButton(text=t("settings.help"), callback_data="settings:help"),
                InlineKeyboardButton(text=t("settings.setup"), callback_data="settings:setup"),
            ],
            [InlineKeyboardButton(text=t("settings.menu"), callback_data="menu")],
        ]
    )


def import_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("import.from_url"), callback_data="import:url"),
                InlineKeyboardButton(text=t("import.from_text"), callback_data="import:text"),
            ],
            [InlineKeyboardButton(text=t("import.pending"), callback_data="import:pending")],
            [InlineKeyboardButton(text=t("menu"), callback_data="menu")],
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
                InlineKeyboardButton(text=t("meal.ok"), callback_data=f"vote:ok:{proposal_id}"),
                InlineKeyboardButton(text=t("meal.no"), callback_data=f"vote:no:{proposal_id}"),
            ]
        )

    rows.extend(
        [
            [
                InlineKeyboardButton(text=t("meal.recipe"), callback_data=f"recipe:{filter_key}:{recipe_id}"),
                InlineKeyboardButton(text=t("meal.shopping"), callback_data=f"shop:{filter_key}:{recipe_id}:{servings}"),
            ],
            [
                InlineKeyboardButton(text=t("meal.next"), callback_data=f"next:{filter_key}"),
                InlineKeyboardButton(text=t("meal.save"), callback_data=f"save:{recipe_id}"),
            ],
        ]
    )

    if proposal_id is None:
        rows.append([InlineKeyboardButton(text=t("meal.reject"), callback_data=f"reject:{filter_key}:{recipe_id}")])

    rows.append([InlineKeyboardButton(text=t("menu"), callback_data="menu")])

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
                InlineKeyboardButton(text=t("meal.recipe"), callback_data=f"recipe:{filter_key}:{recipe_id}"),
                InlineKeyboardButton(text=t("meal.final_list"), callback_data=f"shop:{filter_key}:{recipe_id}:{servings}"),
            ],
            [InlineKeyboardButton(text=t("meal.done"), callback_data=f"done:{proposal_id}")],
            [InlineKeyboardButton(text=t("meal.next"), callback_data=f"next:{filter_key}")],
            [InlineKeyboardButton(text=t("menu"), callback_data="menu")],
        ]
    )


def recipe_keyboard(recipe_id: str, filter_key: str, servings: int = 2) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("meal.shopping"), callback_data=f"shop:{filter_key}:{recipe_id}:{servings}")],
            [
                InlineKeyboardButton(text=t("meal.save"), callback_data=f"save:{recipe_id}"),
                InlineKeyboardButton(text=t("meal.next"), callback_data=f"next:{filter_key}"),
            ],
            [InlineKeyboardButton(text=t("menu"), callback_data="menu")],
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
                InlineKeyboardButton(text=t("meal.recipe"), callback_data=f"recipe:{filter_key}:{recipe_id}"),
                InlineKeyboardButton(text=t("meal.next"), callback_data=f"next:{filter_key}"),
            ],
            [InlineKeyboardButton(text=t("menu"), callback_data="menu")],
        ]
    )


def favorites_keyboard(recipe_ids: list[str]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t("open", number=index + 1), callback_data=f"recipe:any:{recipe_id}")]
        for index, recipe_id in enumerate(recipe_ids)
    ]
    rows.append([InlineKeyboardButton(text=t("menu"), callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def import_drafts_keyboard(drafts: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=t("import.open", title=title), callback_data=f"import:open:{draft_id}")]
        for draft_id, title in drafts
    ]

    rows.append([InlineKeyboardButton(text=t("main.add_recipe"), callback_data="import:menu")])
    rows.append([InlineKeyboardButton(text=t("menu"), callback_data="menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def import_draft_keyboard(draft_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t("import.approve"), callback_data=f"import:approve:{draft_id}"),
                InlineKeyboardButton(text=t("import.reject"), callback_data=f"import:reject:{draft_id}"),
            ],
            [InlineKeyboardButton(text=t("import.yaml"), callback_data=f"import:yaml:{draft_id}")],
            [InlineKeyboardButton(text=t("import.pending"), callback_data="import:pending")],
            [InlineKeyboardButton(text=t("menu"), callback_data="menu")],
        ]
    )
