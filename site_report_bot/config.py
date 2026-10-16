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


settings = Settings()
