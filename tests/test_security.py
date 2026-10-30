"""Zugriffsschutz, Webhook-Signatur, Löschung von Mediendateien und Umgang mit ungültiger LLM-Ausgabe."""

import dataclasses
import hashlib
import hmac
import json
import logging
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from site_report_bot import whatsapp
from site_report_bot.conversation import Conversation
from site_report_bot.llm import LLMOutputError, OllamaProvider
from site_report_bot.log import JsonFormatter, pseudonym
from site_report_bot.pipeline import InputKind, SiteInput
from site_report_bot.telegram_bot import is_allowed

SECRET = "app-secret-fuer-tests"


def _sign(body: bytes, secret: str = SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


# --- Telegram: nur freigeschaltete Chats -----------------------------------------------------


def test_only_allowed_chats_are_accepted():
    assert is_allowed(42, frozenset({42, 7}))
    assert not is_allowed(99, frozenset({42, 7}))


def test_empty_allowlist_blocks_everyone():
    assert not is_allowed(42, frozenset())


# --- WhatsApp: Signatur von Meta -------------------------------------------------------------


def test_signature_valid_and_invalid():
    body = b'{"entry": []}'
    assert whatsapp.signature_valid(body, _sign(body), SECRET)
    assert not whatsapp.signature_valid(body, _sign(body, "falsch"), SECRET)
    assert not whatsapp.signature_valid(body + b" ", _sign(body), SECRET)  # Inhalt verändert


def test_without_secret_every_call_is_rejected():
    body = b"{}"
    assert not whatsapp.signature_valid(body, _sign(body, ""), "")


@pytest.fixture
def client_with_secret(monkeypatch):
    monkeypatch.setattr(whatsapp, "settings", dataclasses.replace(whatsapp.settings, whatsapp_app_secret=SECRET))
    return TestClient(whatsapp.app)


def test_webhook_accepts_signed_payload(client_with_secret):
    body = json.dumps({"entry": []}).encode()
    response = client_with_secret.post("/webhook", content=body, headers={"X-Hub-Signature-256": _sign(body)})
    assert response.status_code == 200


def test_webhook_rejects_forged_payload(client_with_secret):
    body = json.dumps({"entry": []}).encode()
    response = client_with_secret.post("/webhook", content=body, headers={"X-Hub-Signature-256": "sha256=gefaelscht"})
    assert response.status_code == 403


def test_webhook_logs_no_phone_number(client_with_secret, caplog):
    nummer = "491701234567"
    body = json.dumps({"entry": [{"changes": [{"value": {"messages": [
        {"from": nummer, "type": "text", "text": {"body": "Wand gestellt"}}]}}]}]}).encode()
    with caplog.at_level(logging.INFO):
        client_with_secret.post("/webhook", content=body, headers={"X-Hub-Signature-256": _sign(body)})
    protokoll = "\n".join(JsonFormatter().format(r) for r in caplog.records)
    assert nummer not in protokoll
    assert "Wand gestellt" not in protokoll
    assert pseudonym(nummer) in protokoll


# --- Datensparsamkeit: Fotos und Sprachnachrichten werden gelöscht ---------------------------


def _session_with_files(tmp_path) -> tuple[Conversation, list]:
    foto, sprache = tmp_path / "foto.jpg", tmp_path / "sprache.oga"
    foto.write_bytes(b"jpg")
    sprache.write_bytes(b"oga")
    conv = Conversation(report_generator=lambda inputs: tmp_path / "bericht.pdf")
    for item in (SiteInput(InputKind.IMAGE, str(foto)), SiteInput(InputKind.AUDIO, str(sprache)),
                 SiteInput(InputKind.TEXT, "Wand gestellt")):
        list(conv.handle("u1", item))
    return conv, [foto, sprache]


def test_media_deleted_after_report(tmp_path):
    conv, dateien = _session_with_files(tmp_path)
    list(conv.handle("u1", SiteInput(InputKind.TEXT, "Bericht")))
    assert not any(d.exists() for d in dateien)


def test_media_deleted_on_reset(tmp_path):
    conv, dateien = _session_with_files(tmp_path)
    list(conv.handle("u1", SiteInput(InputKind.TEXT, "Neu")))
    assert not any(d.exists() for d in dateien)


def test_media_kept_when_report_fails(tmp_path):
    """Schlägt der Bericht fehl, bleiben die Eingaben erhalten, damit der Handwerker es erneut versuchen kann."""
    conv, dateien = _session_with_files(tmp_path)

    def fehler(inputs):
        raise ValueError("Modell nicht erreichbar")

    conv.report_generator = fehler
    list(conv.handle("u1", SiteInput(InputKind.TEXT, "Bericht")))
    assert all(d.exists() for d in dateien)
    assert len(conv.sessions["u1"]) == 3


# --- LLM: ungültige Ausgabe -------------------------------------------------------------------


class FakeClient:
    def __init__(self, antworten: list[str]):
        self.antworten = antworten
        self.aufrufe = 0

    def chat(self, **kwargs):
        self.aufrufe += 1
        return SimpleNamespace(message=SimpleNamespace(content=self.antworten.pop(0)))


GUELTIG = json.dumps({
    "project_name": "", "site_address": "", "customer_name": "", "trade": "Trockenbau",
    "summary": "Wand gestellt.", "work_performed": ["Wand gestellt"], "materials": [], "labor": [],
    "issues": [], "next_steps": [], "remarks": [],
})


def test_invalid_llm_output_is_retried_once():
    client = FakeClient(["kein json", GUELTIG])
    bericht = OllamaProvider("m", "h", client=client).structure_report(["Wand gestellt"])
    assert bericht.trade == "Trockenbau"
    assert client.aufrufe == 2


def test_invalid_llm_output_raises_readable_error():
    client = FakeClient(["kein json", '{"summary": 5}'])
    with pytest.raises(LLMOutputError, match="nochmal"):
        OllamaProvider("m", "h", client=client).structure_report(["Wand gestellt"])
