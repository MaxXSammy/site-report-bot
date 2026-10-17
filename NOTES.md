# Entwicklungsnotizen

## Modellevaluation (Berichtsstrukturierung)

1. **Das Schema allein reicht nicht:** Mit `format=schema` hat das Modell alle Notizen ins Feld `summary` kopiert. Erst ein Prompt, der jedes Feld erklärt, verteilt die Informationen korrekt.
2. **Ein Textmodell ist nicht besser als ein Vision-Modell:** `qwen2.5:7b` (nur Text) lieferte keine besseren Ergebnisse als `qwen2.5vl:7b`, teils schlechtere ("Ich" als Name, "- " vor Listenpunkten). Entscheidung: ein Modell für Text und Fotos.
3. **Optionale `null`-Felder werden übersprungen:** Bei `str | None` wählte das Modell für Projekt, Adresse und Kunde immer `null`. Lösung: Im LLM-Schema sind alle Felder Pflicht, leere Werte sind `""`.
4. **Pflichtfelder führen zu Halluzinationen:** Bei dünnen Notizen erfand das Modell "Baustelle Müller", 100 Stück Fliesen und 8 Stunden. Der Name stammte wörtlich aus dem Beispiel im Prompt. Lösung: Beispielwerte entfernt, leere Felder ausdrücklich erlaubt, dazu `grounding.py` als deterministische Prüfung gegen die Originalnotizen.
5. **Rollen werden verwechselt:** "Hier ist Müller, Baustelle Schneider" ergab Auftraggeber "Müller". Lösung: Rollenregeln im Prompt (Sprecher = Mitarbeiter). Danach blieb der Auftraggeber oft leer, deshalb leitet der Code ihn aus "Baustelle X" ab.
6. **Freies Gewerk ist uneinheitlich** ("Holzverarbeitung"), Beispiele im Prompt werden übernommen ("Trockenbau"). Lösung: feste Gewerkliste im Prompt.

## Offene Verbesserungen

- Ungefähre Angaben ("ca. 100 Schrauben") werden als exakte Zahl übernommen.
- Einheiten und Nebensätze ("Kunde war zufrieden") gehen je nach Lauf verloren (Schwankung des 7B-Modells).
- Folgeaufgaben bei Mängeln (z. B. "Installateur muss ändern") gehen teilweise verloren.

## Transkription (faster-whisper)

- `small`: Fachbegriffe und Zahlen falsch ("NYM" -> "endy und m", "5. Heute" -> "für den Freute").
- `small` + Fachvokabular als `initial_prompt`: NYM korrekt, Zahlen weiterhin fehlerhaft.
- `medium` + Fachvokabular: fehlerfrei. Entscheidung: `medium` auf der CPU (int8), GPU bleibt frei fürs LLM.
- Ortsnamen ins Vokabular aufgenommen: "Gevelsberg" wurde vorher als "Gefelsberg" erkannt.
- `av` auf 17.1.0 festgelegt: Ab Version 18 fehlt der Parameter `metadata_errors`, den faster-whisper 1.2.1 nutzt.
