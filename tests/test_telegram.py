from site_report_bot.pipeline import InputKind
from site_report_bot.telegram_bot import parse_update


def update_with(message: dict) -> dict:
    return {"update_id": 1, "message": {"chat": {"id": 42}, **message}}


def test_parses_text():
    result = parse_update(update_with({"text": "Bericht"}))
    assert result[0].kind == InputKind.TEXT
    assert result[0].text == "Bericht"
    assert result[0].chat_id == 42


def test_photo_with_caption_gives_image_and_note():
    photo = [{"file_id": "klein"}, {"file_id": "gross"}]
    result = parse_update(update_with({"photo": photo, "caption": "Riss links"}))
    assert [m.kind for m in result] == [InputKind.IMAGE, InputKind.TEXT]
    assert result[0].file_id == "gross"
    assert result[1].text == "Riss links"


def test_parses_voice():
    result = parse_update(update_with({"voice": {"file_id": "v1"}}))
    assert result[0].kind == InputKind.AUDIO
    assert result[0].file_id == "v1"


def test_ignores_updates_without_message():
    assert parse_update({"update_id": 1, "edited_message": {}}) == []
