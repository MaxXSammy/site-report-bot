"""Demo: erzeugt ein Beispiel-PDF über die komplette Pipeline (inkl. Halluzinationsprüfung)."""

import os
from pathlib import Path

from site_report_bot.pipeline import InputKind, SiteInput, generate_report_pdf

notes = [
    "Baustelle Müller, Hauptstraße 12 in Gevelsberg",
    "heute im EG die Trennwand im Bad gestellt, 6 Gipskartonplatten verbraucht und ca 100 Schrauben",
    "Ich und der Lehrling je 7 Stunden",
    "Wasseranschluss sitzt 10 cm zu tief, muss der Installateur ändern",
    "morgen spachteln",
]

inputs = [SiteInput(InputKind.TEXT, note) for note in notes]
path = generate_report_pdf(inputs, output_dir=Path("output"))
print(f"PDF erstellt: {path}")
os.startfile(path.resolve())
