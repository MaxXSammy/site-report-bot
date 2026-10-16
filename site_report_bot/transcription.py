"""Sprachnachrichten lokal in Text umwandeln (faster-whisper, läuft auf der CPU)."""

from functools import lru_cache

from faster_whisper import WhisperModel

from site_report_bot.config import settings


@lru_cache(maxsize=1)
def _get_model() -> WhisperModel:
    """Lädt das Modell nur einmal und hält es danach im Speicher."""
    return WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")


# Fachbegriffe, die Whisper sonst oft falsch erkennt
TRADE_VOCABULARY = (
    "Baustellenbericht. Baustelle, Hausnummer, NYM-Kabel, Gipskarton, Rigips, "
    "Trockenbau, Estrich, Spachteln, Fliesen, Unterverteilung, Steckdosen, "
    "Wasseranschluss, Installateur, Lehrling, Geselle, Stunden, Stück, Rollen, Meter."
)


def transcribe(audio_path: str) -> str:
    segments, _info = _get_model().transcribe(
        audio_path,
        language="de",
        beam_size=5,
        vad_filter=True,
        initial_prompt=TRADE_VOCABULARY,
    )
    return " ".join(segment.text.strip() for segment in segments).strip()
