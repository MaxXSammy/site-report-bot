# Entwicklungsnotizen

## Modellevaluation (Berichtsstrukturierung)

1. **Das Schema allein reicht nicht:** Mit `format=schema` hat das Modell alle Notizen ins Feld `summary` kopiert. Erst ein Prompt, der jedes Feld erklärt, verteilt die Informationen korrekt.
2. **Ein Textmodell ist nicht besser als ein Vision-Modell:** `qwen2.5:7b` (nur Text) lieferte keine besseren Ergebnisse als `qwen2.5vl:7b`, teils schlechtere ("Ich" als Name, "- " vor Listenpunkten). Entscheidung: ein Modell für Text und Fotos.
3. **Optionale `null`-Felder werden übersprungen:** Bei `str | None` wählte das Modell für Projekt, Adresse und Kunde immer `null`. Lösung: Im LLM-Schema sind alle Felder Pflicht, leere Werte sind `""`.

## Offene Verbesserungen

- Ungefähre Angaben ("ca. 100 Schrauben") werden als exakte Zahl übernommen.
- Folgeaufgaben bei Mängeln (z. B. "Installateur muss ändern") gehen teilweise verloren.
