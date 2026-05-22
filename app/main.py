from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from app.bot.handlers.menu import router as menu_router
from app.bot.middleware.language import ChatLanguageMiddleware
from app.settings.config import settings
from app.services.i18n import t



async def set_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description=t("commands.start")),
            BotCommand(command="help", description=t("commands.help")),
            BotCommand(command="import", description=t("commands.import")),
            BotCommand(command="whoami", description=t("commands.whoami")),
            BotCommand(command="setup", description=t("commands.setup")),
        ]
    )


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is empty. Add your BotFather token to .env."
        )

    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    await set_bot_commands(bot)

    dispatcher = Dispatcher()
    dispatcher.message.middleware(ChatLanguageMiddleware())
    dispatcher.callback_query.middleware(ChatLanguageMiddleware())
    dispatcher.include_router(menu_router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
