"""Telegram-Kanal: holt Nachrichten per Long Polling und beantwortet sie."""

import time
from dataclasses import dataclass
from pathlib import Path

import httpx

from site_report_bot.conversation import Conversation, Reply
from site_report_bot.pipeline import InputKind, SiteInput
from site_report_bot.telegram_client import TelegramClient

MEDIA_DIR = Path("media")


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


def to_site_input(client: TelegramClient, msg: TelegramMessage) -> SiteInput:
    if msg.kind == InputKind.TEXT:
        return SiteInput(msg.kind, msg.text)
    path = client.download_file(msg.file_id, MEDIA_DIR / str(msg.chat_id))
    return SiteInput(msg.kind, str(path))


def send_reply(client: TelegramClient, chat_id: int, reply: Reply) -> None:
    if reply.document:
        client.send_document(chat_id, reply.document, caption=reply.text)
    else:
        client.send_message(chat_id, reply.text)


def run() -> None:
    client = TelegramClient()
    conversation = Conversation()
    offset: int | None = None
    print("Telegram-Bot läuft. Beenden mit Strg + C.")

    while True:
        try:
            updates = client.get_updates(offset)
        except httpx.HTTPError as error:
            print(f"Verbindungsproblem ({type(error).__name__}), neuer Versuch in 5 s")
            time.sleep(5)
            continue

        for update in updates:
            offset = update["update_id"] + 1  # bestätigt das Update bei Telegram
            for msg in parse_update(update):
                try:
                    item = to_site_input(client, msg)
                    for reply in conversation.handle(str(msg.chat_id), item):
                        send_reply(client, msg.chat_id, reply)
                except Exception as error:  # ein Fehler darf den Bot nicht beenden
                    print(
                        f"Fehler in Chat {msg.chat_id}: {type(error).__name__}: {error}"
                    )
                    client.send_message(
                        msg.chat_id, "⚠ Da ist etwas schiefgelaufen, bitte nochmal."
                    )


if __name__ == "__main__":
    run()
