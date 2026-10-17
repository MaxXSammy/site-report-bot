"""Schlanker Client für die Telegram Bot API (direkt über httpx, ohne Bibliothek)."""

from pathlib import Path

import httpx

from site_report_bot.config import settings

API_URL = "https://api.telegram.org"


class TelegramError(RuntimeError):
    """Telegram hat eine Anfrage abgelehnt (Antwort mit ok: false)."""


class TelegramClient:
    def __init__(self, token: str = settings.telegram_bot_token) -> None:
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN fehlt in der .env")
        # Der Token steckt in der URL, deshalb diese URLs nie ausgeben oder loggen.
        self.base = f"{API_URL}/bot{token}"
        self.file_base = f"{API_URL}/file/bot{token}"
        self.http = httpx.Client(timeout=60)

    def _call(self, method: str, **kwargs) -> dict | list:
        """Ruft eine Methode der Bot API auf und gibt nur das Ergebnis zurück."""
        response = self.http.post(f"{self.base}/{method}", **kwargs)
        data = response.json()
        if not data.get("ok"):
            raise TelegramError(f"{method}: {data.get('description')}")
        return data["result"]

    def get_updates(self, offset: int | None = None, timeout: int = 30) -> list[dict]:
        """Long Polling: wartet bis zu `timeout` Sekunden auf neue Nachrichten."""
        params: dict = {"timeout": timeout, "allowed_updates": ["message"]}
        if offset is not None:
            params["offset"] = offset
        return self._call("getUpdates", json=params)

    def download_file(self, file_id: str, target_dir: Path) -> Path:
        """Lädt ein Foto oder eine Sprachnachricht herunter (2 Schritte: Pfad holen, Datei laden)."""
        info = self._call("getFile", json={"file_id": file_id})
        remote_path = info[
            "file_path"
        ]  # z. B. "voice/file_3.oga" oder "photos/file_7.jpg"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{file_id}{Path(remote_path).suffix}"
        response = self.http.get(f"{self.file_base}/{remote_path}")
        response.raise_for_status()
        target.write_bytes(response.content)
        return target

    def send_message(self, chat_id: int, text: str) -> None:
        self._call("sendMessage", json={"chat_id": chat_id, "text": text})

    def send_document(self, chat_id: int, path: Path, caption: str = "") -> None:
        with path.open("rb") as file:
            self._call(
                "sendDocument",
                data={"chat_id": chat_id, "caption": caption},
                files={"document": (path.name, file, "application/pdf")},
            )
