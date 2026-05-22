from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from app.db.session import AsyncSessionLocal
from app.services.chat_preferences import get_chat_language
from app.services.i18n import reset_language_context, set_language_context


class ChatLanguageMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        chat_id: int | None = None

        if isinstance(event, Message):
            chat_id = event.chat.id
        elif isinstance(event, CallbackQuery) and event.message:
            chat_id = event.message.chat.id

        token = None

        if chat_id is not None:
            async with AsyncSessionLocal() as session:
                language = await get_chat_language(session, chat_id)
            token = set_language_context(language)

        try:
            return await handler(event, data)
        finally:
            if token is not None:
                reset_language_context(token)
