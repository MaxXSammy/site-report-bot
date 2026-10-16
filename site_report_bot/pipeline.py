"""Pipeline: Eingänge (Text, Sprache, Fotos) -> strukturierter Bericht -> PDF."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

from site_report_bot.llm import LLMProvider, get_provider
from site_report_bot.models import PhotoEntry, SiteReport
from site_report_bot.pdf_report import create_pdf
from site_report_bot.transcription import transcribe


class InputKind(str, Enum):
    TEXT = "text"
    AUDIO = "audio"
    IMAGE = "image"


@dataclass
class SiteInput:
    """Eine einzelne Nachricht vom Handwerker, egal aus welchem Kanal."""

    kind: InputKind
    content: str  # Text bei TEXT, Dateipfad bei AUDIO und IMAGE


def build_report(
    inputs: list[SiteInput],
    provider: LLMProvider | None = None,
    transcriber: Callable[[str], str] = transcribe,
) -> SiteReport:
    provider = provider or get_provider()
    notes: list[str] = []
    photos: list[PhotoEntry] = []

    for item in inputs:
        if item.kind == InputKind.TEXT:
            notes.append(item.content)
        elif item.kind == InputKind.AUDIO:
            notes.append(transcriber(item.content))
        elif item.kind == InputKind.IMAGE:
            caption = provider.describe_photo(item.content)
            photos.append(PhotoEntry(file_path=item.content, caption=caption))

    if not notes:
        raise ValueError(
            "Keine Text- oder Sprachnotizen vorhanden, Bericht kann nicht erstellt werden."
        )

    content = provider.structure_report(notes)
    return SiteReport(**content.model_dump(), photos=photos)


def generate_report_pdf(
    inputs: list[SiteInput],
    output_dir: Path = Path("output"),
    provider: LLMProvider | None = None,
    transcriber: Callable[[str], str] = transcribe,
) -> Path:
    report = build_report(inputs, provider=provider, transcriber=transcriber)
    filename = f"bericht_{datetime.now():%Y%m%d_%H%M%S}.pdf"
    return create_pdf(report, output_dir / filename)
