"""Gesprächslogik: sammelt Eingaben pro Absender und erstellt auf Befehl den Bericht.

Kanalunabhängig: Telegram und WhatsApp übergeben nur SiteInputs, die Antworten
kommen als Reply-Objekte zurück. Wie sie verschickt werden, entscheidet der Kanal.
"""

from collections import defaultdict
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

from site_report_bot.pipeline import InputKind, SiteInput, generate_report_pdf

HELP_TEXT = (
    "So funktioniert's:\n"
    "1. Schick mir Fotos, Sprachnachrichten oder Text zur Baustelle.\n"
    "2. Schreib 'Bericht', dann bekommst du das PDF.\n"
    "3. Mit 'Neu' verwirfst du alle bisherigen Notizen."
)

LABELS = {
    InputKind.TEXT: "Notiz",
    InputKind.AUDIO: "Sprachnachricht",
    InputKind.IMAGE: "Foto",
}


@dataclass
class Reply:
    text: str = ""
    document: Path | None = None


class Conversation:
    def __init__(
        self,
        report_generator: Callable[[list[SiteInput]], Path] = generate_report_pdf,
    ) -> None:
        self.sessions: dict[str, list[SiteInput]] = defaultdict(list)
        self.report_generator = report_generator

    def handle(self, sender: str, item: SiteInput) -> Iterator[Reply]:
        """Verarbeitet eine Nachricht und liefert die Antworten nacheinander."""
        if item.kind == InputKind.TEXT:
            command = item.content.strip().lower().lstrip("/")
            if command == "bericht":
                yield from self._create_report(sender)
                return
            if command == "neu":
                self.sessions.pop(sender, None)
                yield Reply("Alles verworfen. Du kannst neu anfangen.")
                return
            if command in ("hilfe", "help", "start"):
                yield Reply(HELP_TEXT)
                return

        self.sessions[sender].append(item)
        count = len(self.sessions[sender])
        yield Reply(f"✔ {LABELS[item.kind]} gespeichert ({count} Einträge).")

    def _create_report(self, sender: str) -> Iterator[Reply]:
        inputs = self.sessions.get(sender)
        if not inputs:
            yield Reply(
                "Noch keine Notizen da. Schick mir zuerst Text, Sprache oder Fotos."
            )
            return

        yield Reply(f"Erstelle Bericht aus {len(inputs)} Einträgen, das dauert kurz …")
        try:
            pdf = self.report_generator(inputs)
        except ValueError as error:  # z. B. nur Fotos, aber keine Notizen
            yield Reply(f"⚠ {error}")
            return

        self.sessions.pop(sender, None)
        yield Reply("Fertig, hier ist dein Bericht.", document=pdf)
