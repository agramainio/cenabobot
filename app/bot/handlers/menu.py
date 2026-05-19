from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.menu import (
    favorites_keyboard,
    main_menu_keyboard,
    recipe_keyboard,
    shopping_keyboard,
    suggestion_keyboard,
)
from app.db.session import AsyncSessionLocal
from app.services.auth import (
    identity_text,
    is_authorized,
    reject_callback_if_unauthorized,
    reject_message_if_unauthorized,
)
from app.services.formatting import recipe_detail_text, shopping_list_text, suggestion_text
from app.services.recipes import (
    FILTER_LABELS,
    ensure_actor,
    get_favorites,
    get_one_suggestion,
    get_recipe,
    record_feedback,
    save_favorite,
)

router = Router()


async def _ensure_actor_from_message(message: Message) -> None:
    if not message.from_user:
        return

    async with AsyncSessionLocal() as session:
        await ensure_actor(
            session,
            chat_id=message.chat.id,
            chat_title=message.chat.title,
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )


async def _ensure_actor_from_callback(callback: CallbackQuery) -> None:
    if not callback.message or not callback.from_user:
        return

    async with AsyncSessionLocal() as session:
        await ensure_actor(
            session,
            chat_id=callback.message.chat.id,
            chat_title=callback.message.chat.title,
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
        )


@router.message(Command("whoami"))
async def whoami(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else None
    chat_id = message.chat.id if message.chat else None

    await message.answer(
        "Telegram IDs for cenabobot:\n\n"
        f"User ID: <code>{user_id}</code>\n"
        f"Chat ID: <code>{chat_id}</code>\n\n"
        "Add your User ID to ALLOWED_USER_IDS or this Chat ID to ALLOWED_CHAT_IDS in .env."
    )


@router.message(Command("start"))
async def start(message: Message) -> None:
    user_id = message.from_user.id if message.from_user else None
    chat_id = message.chat.id if message.chat else None

    if not is_authorized(user_id, chat_id):
        await message.answer(identity_text(user_id, chat_id))
        return

    await _ensure_actor_from_message(message)
    await message.answer(
        "cenabobot is ready.\n\n"
        "One trusted meal idea at a time.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    if await reject_message_if_unauthorized(message):
        return

    await message.answer(
        "cenabobot is private.\n\n"
        "Use the buttons to get one meal idea, ask for the next idea, open a recipe, "
        "or generate a shopping list.\n\n"
        "Version 1 has no AI and only suggests saved recipes."
    )


@router.callback_query(F.data == "menu")
async def show_menu(callback: CallbackQuery) -> None:
    if await reject_callback_if_unauthorized(callback):
        return

    await _ensure_actor_from_callback(callback)
    await callback.answer()

    if callback.message:
        await callback.message.edit_text(
            "What do you want?",
            reply_markup=main_menu_keyboard(),
        )


@router.callback_query(F.data.startswith("suggest:"))
async def suggest(callback: CallbackQuery) -> None:
    if await reject_callback_if_unauthorized(callback):
        return

    await _ensure_actor_from_callback(callback)
    await callback.answer()

    filter_key = callback.data.split(":", 1)[1] if callback.data else "any"
    await _send_suggestion(callback, filter_key)


@router.callback_query(F.data.startswith("next:"))
async def next_idea(callback: CallbackQuery) -> None:
    if await reject_callback_if_unauthorized(callback):
        return

    await _ensure_actor_from_callback(callback)
    await callback.answer()

    filter_key = callback.data.split(":", 1)[1] if callback.data else "any"
    await _send_suggestion(callback, filter_key)


async def _send_suggestion(callback: CallbackQuery, filter_key: str) -> None:
    if not callback.message:
        return

    filter_key = filter_key if filter_key in FILTER_LABELS else "any"

    async with AsyncSessionLocal() as session:
        recipe = await get_one_suggestion(
            session,
            chat_id=callback.message.chat.id,
            user_id=callback.from_user.id if callback.from_user else None,
            filter_key=filter_key,
        )

    if recipe is None:
        await callback.message.edit_text(
            "No matching saved recipe yet.\n\n"
            "Add more recipes to the catalogue, then try again.",
            reply_markup=main_menu_keyboard(),
        )
        return

    await callback.message.edit_text(
        suggestion_text(recipe, FILTER_LABELS.get(filter_key)),
        reply_markup=suggestion_keyboard(recipe.id, filter_key, recipe.servings),
    )


@router.callback_query(F.data.startswith("recipe:"))
async def show_recipe(callback: CallbackQuery) -> None:
    if await reject_callback_if_unauthorized(callback):
        return

    await callback.answer()

    if not callback.data or not callback.message:
        return

    _, filter_key, recipe_id = callback.data.split(":", 2)

    async with AsyncSessionLocal() as session:
        recipe = await get_recipe(session, recipe_id)

    if recipe is None:
        await callback.message.edit_text("Recipe not found.", reply_markup=main_menu_keyboard())
        return

    await callback.message.edit_text(
        recipe_detail_text(recipe),
        reply_markup=recipe_keyboard(recipe.id, filter_key, recipe.servings),
    )


@router.callback_query(F.data.startswith("shop:"))
async def show_shopping_list(callback: CallbackQuery) -> None:
    if await reject_callback_if_unauthorized(callback):
        return

    await callback.answer()

    if not callback.data or not callback.message:
        return

    _, filter_key, recipe_id, servings_text = callback.data.split(":", 3)

    try:
        servings = int(servings_text)
    except ValueError:
        servings = 2

    async with AsyncSessionLocal() as session:
        recipe = await get_recipe(session, recipe_id)

    if recipe is None:
        await callback.message.edit_text("Recipe not found.", reply_markup=main_menu_keyboard())
        return

    await callback.message.edit_text(
        shopping_list_text(recipe, target_servings=servings),
        reply_markup=shopping_keyboard(recipe.id, filter_key),
    )


@router.callback_query(F.data.startswith("save:"))
async def save(callback: CallbackQuery) -> None:
    if await reject_callback_if_unauthorized(callback):
        return

    if not callback.data or not callback.message or not callback.from_user:
        await callback.answer()
        return

    _, recipe_id = callback.data.split(":", 1)

    async with AsyncSessionLocal() as session:
        created = await save_favorite(
            session,
            chat_id=callback.message.chat.id,
            user_id=callback.from_user.id,
            recipe_id=recipe_id,
        )

    if created:
        await callback.answer("Saved.", show_alert=False)
    else:
        await callback.answer("Already saved.", show_alert=False)


@router.callback_query(F.data.startswith("reject:"))
async def reject(callback: CallbackQuery) -> None:
    if await reject_callback_if_unauthorized(callback):
        return

    await callback.answer("Skipped.", show_alert=False)

    if not callback.data or not callback.message:
        return

    _, filter_key, recipe_id = callback.data.split(":", 2)

    async with AsyncSessionLocal() as session:
        await record_feedback(
            session,
            chat_id=callback.message.chat.id,
            user_id=callback.from_user.id if callback.from_user else None,
            recipe_id=recipe_id,
            feedback_type="not_this",
            reason="not_this",
        )

    await _send_suggestion(callback, filter_key)


@router.callback_query(F.data == "favorites")
async def favorites(callback: CallbackQuery) -> None:
    if await reject_callback_if_unauthorized(callback):
        return

    await callback.answer()

    if not callback.message or not callback.from_user:
        return

    async with AsyncSessionLocal() as session:
        recipes = await get_favorites(
            session,
            chat_id=callback.message.chat.id,
            user_id=callback.from_user.id,
        )

    if not recipes:
        await callback.message.edit_text(
            "No favorites yet.",
            reply_markup=main_menu_keyboard(),
        )
        return

    lines = ["<b>Your favorites</b>", ""]
    for index, recipe in enumerate(recipes, start=1):
        lines.append(f"{index}. {recipe.title}")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=favorites_keyboard([recipe.id for recipe in recipes]),
    )


@router.message()
async def fallback(message: Message) -> None:
    if await reject_message_if_unauthorized(message):
        return

    await message.answer(
        "Use the buttons for now.\n\n"
        "V1 has no AI/free-text parsing yet.",
        reply_markup=main_menu_keyboard(),
    )
