from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChatPreference
from app.services.i18n import fallback_language, normalize_language


async def get_chat_language(session: AsyncSession, chat_id: int) -> str:
    preference = await session.get(ChatPreference, chat_id)

    if preference is None:
        return fallback_language()

    return normalize_language(preference.language)


async def set_chat_language(session: AsyncSession, *, chat_id: int, language: str) -> str:
    normalized = normalize_language(language)
    preference = await session.get(ChatPreference, chat_id)

    if preference is None:
        session.add(ChatPreference(chat_id=chat_id, language=normalized))
    else:
        preference.language = normalized

    await session.commit()
    return normalized
