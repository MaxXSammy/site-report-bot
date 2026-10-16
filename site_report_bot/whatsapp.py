"""WhatsApp-Kanal: empfängt Nachrichten über den Webhook der WhatsApp Cloud API."""

from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from site_report_bot.config import settings

app = FastAPI(title="Site Report Bot")


@dataclass
class IncomingMessage:
    sender: str  # WhatsApp-Nummer des Absenders, z. B. "491701234567"
    kind: str  # "text", "audio" oder "image"
    text: str = ""
    media_id: str = ""


def parse_incoming(payload: dict) -> list[IncomingMessage]:
    """Zieht Text-, Sprach- und Bildnachrichten aus einer Webhook-Payload.

    Statusmeldungen (zugestellt, gelesen, fehlgeschlagen) werden ignoriert.
    """
    messages: list[IncomingMessage] = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            for msg in change.get("value", {}).get("messages", []):
                sender = msg.get("from", "")
                msg_type = msg.get("type")
                if msg_type == "text":
                    messages.append(
                        IncomingMessage(sender, "text", text=msg["text"]["body"])
                    )
                elif msg_type in ("audio", "image"):
                    messages.append(
                        IncomingMessage(sender, msg_type, media_id=msg[msg_type]["id"])
                    )
    return messages


@app.get("/webhook")
def verify_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge"),
) -> PlainTextResponse:
    """Einmalige Prüfung durch Meta beim Einrichten des Webhooks."""
    if mode == "subscribe" and token == settings.whatsapp_verify_token:
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Verifizierung fehlgeschlagen")


@app.post("/webhook")
async def receive_webhook(request: Request) -> dict:
    payload = await request.json()
    for message in parse_incoming(payload):
        print(
            f"[{message.kind}] von {message.sender}: {message.text or message.media_id}"
        )
    return {"status": "ok"}
