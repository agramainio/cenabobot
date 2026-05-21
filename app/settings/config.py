from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_int_csv(value: str) -> set[int]:
    result: set[int] = set()

    for raw_item in value.split(","):
        item = raw_item.strip()
        if not item:
            continue
        try:
            result.add(int(item))
        except ValueError:
            raise ValueError(f"Invalid integer in CSV value: {item}") from None

    return result


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str = ""
    DATABASE_URL: str
    APP_ENV: str = "development"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    ALLOWED_USER_IDS: str = ""
    ALLOWED_CHAT_IDS: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_user_ids(self) -> set[int]:
        return _parse_int_csv(self.ALLOWED_USER_IDS)

    @property
    def allowed_chat_ids(self) -> set[int]:
        return _parse_int_csv(self.ALLOWED_CHAT_IDS)


settings = Settings()
