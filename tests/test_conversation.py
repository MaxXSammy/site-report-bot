from pathlib import Path

from site_report_bot.conversation import Conversation
from site_report_bot.pipeline import InputKind, SiteInput

FAKE_PDF = Path("output/fake.pdf")


def text(content: str) -> SiteInput:
    return SiteInput(InputKind.TEXT, content)


def make_conversation() -> tuple[Conversation, list]:
    received: list = []

    def fake_generator(inputs: list[SiteInput]) -> Path:
        received.append(inputs)
        return FAKE_PDF

    return Conversation(report_generator=fake_generator), received


def test_collects_inputs_until_report():
    conv, received = make_conversation()
    list(conv.handle("u1", text("Wand im Bad verputzt")))
    list(conv.handle("u1", SiteInput(InputKind.IMAGE, "foto.jpg")))

    replies = list(conv.handle("u1", text("Bericht")))

    assert replies[-1].document == FAKE_PDF
    assert len(received[0]) == 2
    assert "u1" not in conv.sessions


def test_new_discards_notes():
    conv, _ = make_conversation()
    list(conv.handle("u1", text("Notiz")))
    list(conv.handle("u1", text("/neu")))
    assert "u1" not in conv.sessions


def test_report_without_notes_gives_hint():
    conv, received = make_conversation()
    replies = list(conv.handle("u1", text("Bericht")))
    assert replies[0].document is None
    assert received == []


def test_senders_are_kept_separate():
    conv, _ = make_conversation()
    list(conv.handle("u1", text("Notiz A")))
    list(conv.handle("u2", text("Notiz B")))
    assert len(conv.sessions["u1"]) == 1
    assert len(conv.sessions["u2"]) == 1
