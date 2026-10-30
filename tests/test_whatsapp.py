import dataclasses

from fastapi.testclient import TestClient

from site_report_bot import whatsapp
from site_report_bot.config import settings
from site_report_bot.whatsapp import app, parse_incoming

client = TestClient(app)


def _payload(messages=None, statuses=None):
    value = {"messaging_product": "whatsapp"}
    if messages:
        value["messages"] = messages
    if statuses:
        value["statuses"] = statuses
    return {
        "object": "whatsapp_business_account",
        "entry": [{"changes": [{"value": value, "field": "messages"}]}],
    }


def test_parse_text_audio_image():
    payload = _payload(
        messages=[
            {"from": "491701234567", "type": "text", "text": {"body": "Wand gestellt"}},
            {"from": "491701234567", "type": "audio", "audio": {"id": "AUDIO123"}},
            {"from": "491701234567", "type": "image", "image": {"id": "IMG456"}},
        ]
    )
    result = parse_incoming(payload)
    assert [m.kind for m in result] == ["text", "audio", "image"]
    assert result[0].text == "Wand gestellt"
    assert result[1].media_id == "AUDIO123"


def test_status_updates_are_ignored():
    payload = _payload(statuses=[{"status": "failed"}])
    assert parse_incoming(payload) == []


def test_webhook_verification_success(monkeypatch):
    monkeypatch.setattr(whatsapp, "settings", dataclasses.replace(settings, whatsapp_verify_token="geheim"))
    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "geheim",
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 200
    assert response.text == "12345"


def test_webhook_verification_without_configured_token():
    """Ohne Verify-Token in der .env darf auch ein leeres Token nicht durchgehen."""
    response = client.get(
        "/webhook",
        params={"hub.mode": "subscribe", "hub.verify_token": "", "hub.challenge": "12345"},
    )
    assert response.status_code == 403


def test_webhook_verification_wrong_token():
    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "falsch",
            "hub.challenge": "12345",
        },
    )
    assert response.status_code == 403
