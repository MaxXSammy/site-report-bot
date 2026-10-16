import os
from pathlib import Path

from site_report_bot.llm import get_provider
from site_report_bot.models import SiteReport
from site_report_bot.pdf_report import create_pdf

notes = [
    "Baustelle Müller, Hauptstraße 12 in Gevelsberg",
    "heute im EG die Trennwand im Bad gestellt, 6 Gipskartonplatten verbraucht und ca 100 Schrauben",
    "Ich und der Lehrling je 7 Stunden",
    "Wasseranschluss sitzt 10 cm zu tief, muss der Installateur ändern",
    "morgen spachteln",
]

content = get_provider().structure_report(notes)
report = SiteReport(**content.model_dump())
path = create_pdf(report, Path("output/demo_bericht.pdf"))
print(f"PDF erstellt: {path}")
os.startfile(path.resolve())
