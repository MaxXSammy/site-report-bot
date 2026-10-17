"""Schutz vor Halluzinationen: entfernt Angaben, die nicht in den Notizen stehen.

Kleine LLMs füllen Pflichtfelder gern mit plausiblen, aber erfundenen Werten.
Diese Prüfung ist deterministisch und gilt unabhängig vom LLM-Anbieter.
"""

import re

from site_report_bot.models import ReportContent

# Allgemeine Wörter, die allein keinen Namen belegen ("Baustelle Müller" braucht "Müller")
GENERIC_WORDS = {
    "baustelle",
    "bauvorhaben",
    "projekt",
    "herr",
    "frau",
    "familie",
    "firma",
}

# Whisper schreibt Zahlen manchmal als Wort ("acht Stunden")
NUMBER_WORDS = {
    "ein": 1,
    "eine": 1,
    "eins": 1,
    "zwei": 2,
    "drei": 3,
    "vier": 4,
    "fünf": 5,
    "sechs": 6,
    "sieben": 7,
    "acht": 8,
    "neun": 9,
    "zehn": 10,
    "elf": 11,
    "zwölf": 12,
    "zwanzig": 20,
    "dreißig": 30,
    "fünfzig": 50,
    "hundert": 100,
}


def _numbers_in(text: str) -> set[float]:
    digits = {float(n.replace(",", ".")) for n in re.findall(r"\d+(?:[.,]\d+)?", text)}
    words = {float(NUMBER_WORDS[w]) for w in _words_in(text) if w in NUMBER_WORDS}
    return digits | words


def _words_in(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def _is_supported(value: str, note_words: set[str]) -> bool:
    """True, wenn jedes aussagekräftige Wort des Werts auch in den Notizen vorkommt."""
    relevant = [
        w
        for w in re.findall(r"\w+", value.lower())
        if len(w) >= 3 and w not in GENERIC_WORDS
    ]
    return bool(relevant) and all(w in note_words for w in relevant)


def fill_customer_from_project(content: ReportContent) -> ReportContent:
    """'Baustelle Schneider' ohne Auftraggeber -> Auftraggeber 'Schneider'.

    Deterministisch statt per LLM: Kleine Modelle lassen das Feld sonst oft leer.
    """
    if content.customer_name:
        return content
    words = content.project_name.split()
    if len(words) >= 2 and words[0].lower() in GENERIC_WORDS:
        content.customer_name = " ".join(words[1:])
    return content


def remove_unsupported(content: ReportContent, notes: list[str]) -> ReportContent:
    text = " ".join(notes)
    note_words = _words_in(text)
    numbers = _numbers_in(text)

    for field in ("project_name", "customer_name"):
        value = getattr(content, field)
        if value and not _is_supported(value, note_words):
            setattr(content, field, "")

    for material in content.materials:
        if material.quantity is not None and material.quantity not in numbers:
            material.quantity = None
            material.unit = None

    content.labor = [entry for entry in content.labor if entry.hours in numbers]
    return content
