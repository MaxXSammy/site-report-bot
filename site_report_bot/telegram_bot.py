"""Telegram-Kanal: holt Nachrichten per Long Polling und beantwortet sie."""

import logging
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

from site_report_bot.config import settings
from site_report_bot.conversation import Conversation, Reply
from site_report_bot.log import pseudonym
from site_report_bot.pipeline import InputKind, SiteInput
from site_report_bot.telegram_client import TelegramClient

MEDIA_DIR = Path("media")

logger = logging.getLogger(__name__)


@dataclass
class TelegramMessage:
    chat_id: int
    kind: InputKind
    text: str = ""
    file_id: str = ""


def parse_update(update: dict) -> list[TelegramMessage]:
    """Zieht Text, Fotos und Sprachnachrichten aus einem Telegram-Update.

    Ein Foto mit Bildunterschrift ergibt zwei Einträge: das Bild und die Notiz.
    """
    message = update.get("message")
    if not message:
        return []

    chat_id = message["chat"]["id"]
    if "text" in message:
        return [TelegramMessage(chat_id, InputKind.TEXT, text=message["text"])]

    result: list[TelegramMessage] = []
    if "photo" in message:
        largest = message["photo"][
            -1
        ]  # Telegram liefert mehrere Größen, die letzte ist die größte
        result.append(
            TelegramMessage(chat_id, InputKind.IMAGE, file_id=largest["file_id"])
        )
    elif "voice" in message or "audio" in message:
        media = message.get("voice") or message.get("audio")
        result.append(
            TelegramMessage(chat_id, InputKind.AUDIO, file_id=media["file_id"])
        )

    if message.get("caption"):
        result.append(TelegramMessage(chat_id, InputKind.TEXT, text=message["caption"]))
    return result


def is_allowed(chat_id: int, allowed: frozenset[int] | None = None) -> bool:
    """Nur freigeschaltete Chats dürfen den Bot nutzen. Ohne Liste ist niemand freigeschaltet."""
    return chat_id in (settings.telegram_allowed_chat_ids if allowed is None else allowed)


def to_site_input(client: TelegramClient, msg: TelegramMessage) -> SiteInput:
    if msg.kind == InputKind.TEXT:
        return SiteInput(msg.kind, msg.text)
    path = client.download_file(msg.file_id, MEDIA_DIR / str(msg.chat_id))
    return SiteInput(msg.kind, str(path))


def send_reply(client: TelegramClient, chat_id: int, reply: Reply) -> None:
    if reply.document:
        client.send_document(chat_id, reply.document, caption=reply.text)
        # Das PDF liegt jetzt beim Handwerker, eine Kopie auf dem Server braucht es nicht
        reply.document.unlink(missing_ok=True)
    else:
        client.send_message(chat_id, reply.text)


def run() -> None:
    client = TelegramClient()
    conversation = Conversation()
    offset: int | None = None
    # Sitzungen liegen nur im Arbeitsspeicher. Dateien aus einem früheren Lauf gehören zu keiner Sitzung mehr.
    shutil.rmtree(MEDIA_DIR, ignore_errors=True)
    if not settings.telegram_allowed_chat_ids:
        logger.warning("TELEGRAM_ALLOWED_CHAT_IDS ist leer, der Bot nimmt von niemandem Nachrichten an")
    logger.info("Telegram-Bot läuft, beenden mit Strg + C")

    while True:
        try:
            updates = client.get_updates(offset)
        except httpx.HTTPError as error:
            logger.warning("Verbindungsproblem, neuer Versuch in 5 s", extra={"fehler": type(error).__name__})
            time.sleep(5)
            continue

        for update in updates:
            offset = update["update_id"] + 1  # bestätigt das Update bei Telegram
            for msg in parse_update(update):
                chat = pseudonym(msg.chat_id)
                if not is_allowed(msg.chat_id):
                    logger.warning("Nachricht von nicht freigeschaltetem Chat abgelehnt", extra={"chat": chat})
                    client.send_message(
                        msg.chat_id,
                        f"Dieser Chat ist nicht freigeschaltet. Deine Chat-ID: {msg.chat_id}. "
                        "Bitte beim Administrator freischalten lassen.",
                    )
                    continue
                logger.info("Nachricht empfangen", extra={"chat": chat, "art": msg.kind.value})
                try:
                    item = to_site_input(client, msg)
                    for reply in conversation.handle(str(msg.chat_id), item):
                        send_reply(client, msg.chat_id, reply)
                except Exception as error:  # ein Fehler darf den Bot nicht beenden
                    logger.exception("Fehler bei der Verarbeitung", extra={"chat": chat, "fehler": type(error).__name__})
                    client.send_message(
                        msg.chat_id, "⚠ Da ist etwas schiefgelaufen, bitte nochmal."
                    )


if __name__ == "__main__":
    run()
