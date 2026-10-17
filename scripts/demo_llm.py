"""Demo: zeigt die ROHE Ausgabe des LLM, ohne Halluzinationsprüfung (zum Vergleich)."""

from site_report_bot.llm import get_provider

notes = [
    "Baustelle Müller, Hauptstraße 12 in Gevelsberg",
    "heute im EG die Trennwand im Bad gestellt, 6 Gipskartonplatten verbraucht und ca 100 Schrauben",
    "Ich und der Lehrling je 7 Stunden",
    "Wasseranschluss sitzt 10 cm zu tief, muss der Installateur ändern",
    "morgen spachteln",
]

report = get_provider().structure_report(notes)
print(report.model_dump_json(indent=2))
