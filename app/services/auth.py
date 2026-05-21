from __future__ import annotations

from aiogram.types import CallbackQuery, Message

from app.settings.config import settings


def is_authorized(user_id: int | None, chat_id: int | None) -> bool:
    if user_id is None or chat_id is None:
        return False

    if user_id in settings.allowed_user_ids:
        return True

    if chat_id in settings.allowed_chat_ids:
        return True

    return False



def is_trusted_user(user_id: int | None) -> bool:
    if user_id is None:
        return False

    return user_id in settings.allowed_user_ids


def trusted_user_required_text(user_id: int | None) -> str:
    return (
        "Cette action est réservée aux utilisateurs autorisés.\n\n"
        "Pour autoriser cette personne, ajoute son User ID à ALLOWED_USER_IDS "
        "dans .env.production sur le VPS, puis redémarre le bot.\n\n"
        f"User ID : <code>{user_id or ''}</code>"
    )


async def reject_message_if_untrusted_user(message: Message) -> bool:
    user_id = message.from_user.id if message.from_user else None

    if is_trusted_user(user_id):
        return False

    await message.answer(trusted_user_required_text(user_id))
    return True


async def reject_callback_if_untrusted_user(callback: CallbackQuery) -> bool:
    user_id = callback.from_user.id if callback.from_user else None

    if is_trusted_user(user_id):
        return False

    await callback.answer(
        "Cette action est réservée aux utilisateurs autorisés.",
        show_alert=True,
    )
    return True


def identity_text(user_id: int | None, chat_id: int | None) -> str:
    return (
        "This bot is private.\n\n"
        "To allow this chat, add one of these values to .env:\n\n"
        f"ALLOWED_USER_IDS={user_id or ''}\n"
        f"ALLOWED_CHAT_IDS={chat_id or ''}"
    )


async def reject_message_if_unauthorized(message: Message) -> bool:
    user_id = message.from_user.id if message.from_user else None
    chat_id = message.chat.id if message.chat else None

    if is_authorized(user_id, chat_id):
        return False

    await message.answer(identity_text(user_id, chat_id))
    return True


async def reject_callback_if_unauthorized(callback: CallbackQuery) -> bool:
    user_id = callback.from_user.id if callback.from_user else None
    chat_id = callback.message.chat.id if callback.message else None

    if is_authorized(user_id, chat_id):
        return False

    await callback.answer("This bot is private.", show_alert=True)
    return True
