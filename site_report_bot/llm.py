"""LLM-Schicht: macht aus Rohnotizen einen strukturierten Baustellenbericht."""

from typing import Protocol

import ollama

from site_report_bot.config import settings
from site_report_bot.models import ReportContent

SYSTEM_PROMPT = """Du bist Assistent für Baustellendokumentation im Handwerk.
Du erhältst Notizen eines Handwerkers (Textnachrichten und transkribierte Sprachnachrichten).
Verteile die Informationen auf die passenden Felder des Berichts:

- project_name: Bezeichnung des Bauvorhabens, z. B. "Baustelle Müller"
- site_address: Adresse der Baustelle
- customer_name: Auftraggeber (aus "Baustelle Müller" folgt "Müller")
- trade: Gewerk, abgeleitet aus den Arbeiten (z. B. Gipskartonwand -> Trockenbau)
- summary: 2-3 eigene, ausformulierte Sätze. Kopiere NICHT die Notizen.
- work_performed: jede erledigte Arbeit als eigener Listenpunkt
- materials: jedes Material einzeln, mit Menge und Einheit, falls genannt
- labor: jede Person einzeln mit ihren Stunden
- issues: Mängel, Probleme, Behinderungen
- next_steps: was als Nächstes geplant ist

Regeln:
- Jede Information gehört in genau ein passendes Feld, nicht alles in summary.
- Übernimm nur Informationen aus den Notizen. Erfinde nichts.
- Fehlt eine Angabe, nutze einen leeren Text "" bzw. eine leere Liste.
- Schreibe sachlich und professionell auf Deutsch.
- Ändere niemals Mengen, Zahlen oder Namen."""


def _llm_schema() -> dict:
    """Schema für das LLM: alle Felder sind Pflicht, damit nichts übersprungen wird."""
    schema = ReportContent.model_json_schema()
    schema["required"] = list(schema["properties"])
    return schema


class LLMProvider(Protocol):
    """Schnittstelle, die jeder LLM-Anbieter erfüllen muss (Ollama, Claude, Gemini ...)."""

    def structure_report(self, notes: list[str]) -> ReportContent: ...

    def describe_photo(self, image_path: str) -> str: ...


class OllamaProvider:
    def __init__(self, model: str, host: str) -> None:
        self.model = model
        self.client = ollama.Client(host=host)

    def structure_report(self, notes: list[str]) -> ReportContent:
        notes_text = "\n".join(f"- {note}" for note in notes)
        response = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Notizen vom Tag:\n{notes_text}"},
            ],
            format=_llm_schema(),
            options={"temperature": 0},
        )
        return ReportContent.model_validate_json(response.message.content)

    def describe_photo(self, image_path: str) -> str:
        response = self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": "Beschreibe sachlich in einem Satz, was auf diesem Baustellenfoto zu sehen ist.",
                    "images": [image_path],
                }
            ],
            options={"temperature": 0},
        )
        return response.message.content.strip()


def get_provider() -> LLMProvider:
    """Wählt den Anbieter anhand von LLM_PROVIDER in der .env."""
    if settings.llm_provider == "ollama":
        return OllamaProvider(model=settings.ollama_model, host=settings.ollama_host)
    raise ValueError(f"Unbekannter LLM_PROVIDER: {settings.llm_provider}")
