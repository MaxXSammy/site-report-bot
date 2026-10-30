"""LLM-Schicht: macht aus Rohnotizen einen strukturierten Baustellenbericht."""

import logging
from typing import Protocol

import ollama
from pydantic import ValidationError

from site_report_bot.config import settings
from site_report_bot.models import ReportContent

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Du bist Assistent für Baustellendokumentation im Handwerk.
Du erhältst Notizen eines Handwerkers (Textnachrichten und transkribierte Sprachnachrichten).
Verteile die Informationen auf die passenden Felder des Berichts:

- project_name: Bezeichnung des Bauvorhabens, nur wenn genannt ("Baustelle X" -> "Baustelle X")
- site_address: Adresse der Baustelle, nur wenn genannt
- customer_name: Auftraggeber = Kunde, bei dem gearbeitet wird, nur wenn genannt
- trade: genau EIN Gewerk aus dieser Liste, das am besten zu den Arbeiten passt:
  Innenausbau, Trockenbau, Maler, Fliesen, Bodenbelag, Tischler, Elektro,
  Sanitär, Heizung, Dachdecker, Maurer, Garten- und Landschaftsbau
- summary: 2-3 eigene, ausformulierte Sätze. Kopiere NICHT die Notizen.
- work_performed: jede erledigte Arbeit als eigener Listenpunkt
- materials: jedes genannte Material einzeln; Menge und Einheit nur, wenn genannt
- labor: nur wenn Person UND Stunden genannt sind, sonst leere Liste.
  Als worker den genannten Namen eintragen, nicht die Rolle.
- issues: Mängel, Probleme, Behinderungen
- next_steps: was als Nächstes geplant ist
- remarks: Abnahmen, Absprachen und Rückmeldungen des Kunden, sonstige Bemerkungen

Rollen unterscheiden:
- Wer sich vorstellt ("Hier ist X", "Ich bin X", "X hier"), ist ein MITARBEITER,
  niemals der Auftraggeber. Mit "ich" ist diese Person gemeint.
- "Baustelle X", "bei X", "Kunde X", "Familie X" bezeichnen den AUFTRAGGEBER X.
- Ein Mitarbeitername gehört nur in labor, nicht in customer_name oder project_name.

Regeln:
- Jede Information gehört in genau ein passendes Feld, nicht alles in summary.
- Übernimm nur Informationen aus den Notizen. Erfinde nichts.
- Fehlt eine Angabe, nutze einen leeren Text "" bzw. eine leere Liste.
- Leere Felder sind richtig und erwünscht. Ein erfundener Name, eine erfundene
  Menge oder erfundene Stunden sind ein schwerer Fehler.
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


class LLMOutputError(ValueError):
    """Das Modell hat auch nach erneutem Versuch keinen gültigen Bericht geliefert."""


class OllamaProvider:
    def __init__(self, model: str, host: str, client: ollama.Client | None = None, attempts: int = 2) -> None:
        self.model = model
        # Timeout: Hängt das Modell, soll der Bot nach 2 Minuten antworten statt ewig zu warten
        self.client = client or ollama.Client(host=host, timeout=120)
        self.attempts = attempts

    def structure_report(self, notes: list[str]) -> ReportContent:
        notes_text = "\n".join(f"- {note}" for note in notes)
        for attempt in range(1, self.attempts + 1):
            response = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Notizen vom Tag:\n{notes_text}"},
                ],
                format=_llm_schema(),
                # num_predict begrenzt die Ausgabe: Eine Endlosschleife des Modells bricht ab, statt den Bot zu blockieren
                options={"temperature": 0, "num_predict": 2048},
            )
            try:
                return ReportContent.model_validate_json(response.message.content)
            except ValidationError as error:
                logger.warning("Ungültige LLM-Ausgabe", extra={"fehler": f"Versuch {attempt}: {error.error_count()} Felder"})
        raise LLMOutputError("Das Modell hat keinen gültigen Bericht geliefert. Bitte schick nochmal 'Bericht'.")

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
            options={"temperature": 0, "num_predict": 200},
        )
        return response.message.content.strip()


def get_provider() -> LLMProvider:
    """Wählt den Anbieter anhand von LLM_PROVIDER in der .env."""
    if settings.llm_provider == "ollama":
        return OllamaProvider(model=settings.ollama_model, host=settings.ollama_host)
    raise ValueError(f"Unbekannter LLM_PROVIDER: {settings.llm_provider}")
