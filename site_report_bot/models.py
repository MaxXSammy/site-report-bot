"""Datenmodell eines Baustellenberichts."""

from datetime import date

from pydantic import BaseModel, Field


class MaterialItem(BaseModel):
    name: str = Field(description="Bezeichnung des Materials, z. B. 'Gipskartonplatte 12,5 mm'")
    quantity: float | None = Field(default=None, description="Menge, nur falls genannt")
    unit: str | None = Field(default=None, description="Einheit, z. B. Stück, m², kg, lfm")


class LaborEntry(BaseModel):
    worker: str = Field(description="Name oder Rolle, z. B. 'Geselle' oder 'Max'")
    hours: float = Field(description="Geleistete Arbeitsstunden")


class ReportContent(BaseModel):
    """Felder, die das LLM aus den Nachrichten des Handwerkers extrahiert."""

    project_name: str | None = Field(default=None, description="Name des Bauvorhabens")
    site_address: str | None = Field(default=None, description="Adresse der Baustelle")
    customer_name: str | None = Field(default=None, description="Name des Auftraggebers")
    trade: str | None = Field(default=None, description="Gewerk, z. B. Trockenbau, Elektro, Sanitär")
    summary: str = Field(description="Zusammenfassung des Arbeitstages in 2-3 Sätzen")
    work_performed: list[str] = Field(default_factory=list, description="Erledigte Arbeiten, je ein Punkt")
    materials: list[MaterialItem] = Field(default_factory=list, description="Verbrauchtes Material")
    labor: list[LaborEntry] = Field(default_factory=list, description="Arbeitszeiten")
    issues: list[str] = Field(default_factory=list, description="Mängel, Probleme, Behinderungen")
    next_steps: list[str] = Field(default_factory=list, description="Geplante nächste Schritte")


class PhotoEntry(BaseModel):
    file_path: str
    caption: str = Field(description="Kurze Beschreibung, was auf dem Foto zu sehen ist")


class SiteReport(ReportContent):
    """Vollständiger Bericht: LLM-Inhalt plus Daten, die das System selbst setzt."""

    report_date: date = Field(default_factory=date.today)
    photos: list[PhotoEntry] = Field(default_factory=list)