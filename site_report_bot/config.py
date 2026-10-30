"""Zentrale Konfiguration, geladen aus der .env-Datei."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    llm_provider: str = os.getenv("LLM_PROVIDER", "ollama")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5vl:7b")
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    whisper_model: str = os.getenv("WHISPER_MODEL", "medium")

    whatsapp_access_token: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    whatsapp_phone_number_id: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    whatsapp_verify_token: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
    # Mit diesem Schlüssel signiert Meta jeden Webhook-Aufruf (Header X-Hub-Signature-256)
    whatsapp_app_secret: str = os.getenv("WHATSAPP_APP_SECRET", "")

    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    # Nur diese Chats dürfen den Bot nutzen (kommagetrennte IDs). Leer heißt: niemand.
    telegram_allowed_chat_ids: frozenset[int] = frozenset(
        int(chat_id) for chat_id in os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "").split(",") if chat_id.strip()
    )

    log_level: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
