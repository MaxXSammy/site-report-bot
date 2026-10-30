"""WhatsApp-Kanal: empfängt Nachrichten über den Webhook der WhatsApp Cloud API."""

import hashlib
import hmac
import json
import logging
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from site_report_bot.config import settings
from site_report_bot.log import pseudonym

app = FastAPI(title="Site Report Bot")

logger = logging.getLogger(__name__)


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


def signature_valid(body: bytes, signature: str, secret: str | None = None) -> bool:
    """Prüft die Signatur, mit der Meta jeden Aufruf unterschreibt (HMAC-SHA256 über den Rohinhalt).

    Ohne konfiguriertes App-Secret wird jeder Aufruf abgelehnt: lieber nichts annehmen als alles.
    """
    secret = settings.whatsapp_app_secret if secret is None else secret
    if not secret:
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)  # zeitkonstanter Vergleich gegen Timing-Angriffe


@app.get("/webhook")
def verify_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge"),
) -> PlainTextResponse:
    """Einmalige Prüfung durch Meta beim Einrichten des Webhooks."""
    if mode == "subscribe" and settings.whatsapp_verify_token and hmac.compare_digest(token, settings.whatsapp_verify_token):
        return PlainTextResponse(challenge)
    raise HTTPException(status_code=403, detail="Verifizierung fehlgeschlagen")


@app.post("/webhook")
async def receive_webhook(request: Request) -> dict:
    body = await request.body()
    if not signature_valid(body, request.headers.get("X-Hub-Signature-256", "")):
        logger.warning("Webhook-Aufruf mit ungültiger Signatur abgelehnt")
        raise HTTPException(status_code=403, detail="Ungültige Signatur")
    for message in parse_incoming(json.loads(body)):
        # Telefonnummer und Inhalt gehören nicht ins Protokoll
        logger.info("Nachricht empfangen", extra={"chat": pseudonym(message.sender), "art": message.kind})
    return {"status": "ok"}
