import pytest

from site_report_bot.models import ReportContent
from site_report_bot.pipeline import (
    InputKind,
    SiteInput,
    build_report,
    generate_report_pdf,
)


class FakeProvider:
    def __init__(self):
        self.received_notes = []

    def structure_report(self, notes):
        self.received_notes = notes
        return ReportContent(summary="Testbericht", work_performed=notes)

    def describe_photo(self, image_path):
        return f"Foto von {image_path}"


def fake_transcriber(path):
    return f"Transkript von {path}"


def test_build_report_combines_all_inputs():
    provider = FakeProvider()
    inputs = [
        SiteInput(InputKind.TEXT, "Wand gestellt"),
        SiteInput(InputKind.AUDIO, "sprachnachricht.ogg"),
        SiteInput(InputKind.IMAGE, "foto.jpg"),
    ]
    report = build_report(inputs, provider=provider, transcriber=fake_transcriber)

    assert provider.received_notes == [
        "Wand gestellt",
        "Transkript von sprachnachricht.ogg",
    ]
    assert len(report.photos) == 1
    assert report.photos[0].caption == "Foto von foto.jpg"


def test_build_report_without_notes_raises():
    with pytest.raises(ValueError):
        build_report([SiteInput(InputKind.IMAGE, "foto.jpg")], provider=FakeProvider())


def test_generate_report_pdf(tmp_path):
    inputs = [SiteInput(InputKind.TEXT, "Wand gestellt")]
    path = generate_report_pdf(inputs, output_dir=tmp_path, provider=FakeProvider())
    assert path.exists()
