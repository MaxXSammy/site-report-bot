"""Erzeugt aus einem SiteReport einen professionellen PDF-Bericht."""

from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from site_report_bot.models import SiteReport

WINDOWS_FONTS = Path("C:/Windows/Fonts")
PRIMARY_COLOR = (30, 60, 110)


def _fmt_number(value: float | None) -> str:
    """6.0 -> '6', 2.5 -> '2,5', None -> ''."""
    if value is None:
        return ""
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").replace(".", ",")


class ReportPDF(FPDF):
    def __init__(self) -> None:
        super().__init__(format="A4")
        self.set_margins(20, 20, 20)
        self.set_auto_page_break(auto=True, margin=20)
        self.font_name = self._register_fonts()
        self.bullet = "•" if self.font_name == "Arial" else "-"

    def _register_fonts(self) -> str:
        """Arial (Unicode) wenn vorhanden, sonst Helvetica als Fallback."""
        regular = WINDOWS_FONTS / "arial.ttf"
        bold = WINDOWS_FONTS / "arialbd.ttf"
        if regular.exists() and bold.exists():
            self.add_font("Arial", "", str(regular))
            self.add_font("Arial", "B", str(bold))
            return "Arial"
        return "Helvetica"

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font(self.font_name, "", 8)
        self.set_text_color(120)
        self.cell(0, 10, f"Seite {self.page_no()}/{{nb}}", align="C")

    def body_font(self) -> None:
        self.set_font(self.font_name, "", 10)
        self.set_text_color(0)

    def section_title(self, title: str) -> None:
        self.ln(4)
        self.set_font(self.font_name, "B", 12)
        self.set_text_color(*PRIMARY_COLOR)
        self.cell(0, 8, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_draw_color(*PRIMARY_COLOR)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)
        self.body_font()

    def paragraph(self, text: str) -> None:
        self.multi_cell(0, 6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    def bullet_list(self, items: list[str]) -> None:
        if not items:
            self.paragraph("Keine Angaben")
            return
        for item in items:
            self.cell(6, 6, self.bullet)
            self.multi_cell(0, 6, item, new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def create_pdf(report: SiteReport, output_path: Path) -> Path:
    pdf = ReportPDF()
    pdf.add_page()

    # Titel
    pdf.set_font(pdf.font_name, "B", 20)
    pdf.set_text_color(*PRIMARY_COLOR)
    pdf.cell(0, 12, "Baustellenbericht", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.body_font()
    pdf.cell(
        0,
        6,
        f"Datum: {report.report_date:%d.%m.%Y}",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
    )

    # Kopfdaten
    pdf.section_title("Projektdaten")
    with pdf.table(
        col_widths=(45, 125), first_row_as_headings=False, borders_layout="NONE"
    ) as table:
        for label, value in [
            ("Bauvorhaben", report.project_name),
            ("Adresse", report.site_address),
            ("Auftraggeber", report.customer_name),
            ("Gewerk", report.trade),
        ]:
            row = table.row()
            row.cell(label)
            row.cell(value or "-")

    pdf.section_title("Zusammenfassung")
    pdf.paragraph(report.summary)

    pdf.section_title("Ausgeführte Arbeiten")
    pdf.bullet_list(report.work_performed)

    pdf.section_title("Material")
    if report.materials:
        with pdf.table(col_widths=(100, 35, 35)) as table:
            header = table.row()
            for heading in ("Material", "Menge", "Einheit"):
                header.cell(heading)
            for item in report.materials:
                row = table.row()
                row.cell(item.name)
                row.cell(_fmt_number(item.quantity))
                row.cell(item.unit or "")
    else:
        pdf.paragraph("Keine Angaben")

    pdf.section_title("Arbeitszeiten")
    if report.labor:
        with pdf.table(col_widths=(120, 50)) as table:
            header = table.row()
            header.cell("Mitarbeiter")
            header.cell("Stunden")
            for entry in report.labor:
                row = table.row()
                row.cell(entry.worker)
                row.cell(_fmt_number(entry.hours))
            total = table.row()
            total.cell("Gesamt")
            total.cell(_fmt_number(sum(e.hours for e in report.labor)))
    else:
        pdf.paragraph("Keine Angaben")

    pdf.section_title("Mängel und Probleme")
    pdf.bullet_list(report.issues)

    pdf.section_title("Nächste Schritte")
    pdf.bullet_list(report.next_steps)

    # Fotos
    photos = [p for p in report.photos if Path(p.file_path).exists()]
    if photos:
        pdf.section_title("Fotodokumentation")
        for photo in photos:
            if pdf.get_y() + 75 > pdf.page_break_trigger:
                pdf.add_page()
            pdf.image(photo.file_path, w=80, h=60, keep_aspect_ratio=True)
            pdf.paragraph(photo.caption)
            pdf.ln(3)

    # Unterschriftsfeld (Vorbereitung für Stufe 2)
    if pdf.get_y() + 30 > pdf.page_break_trigger:
        pdf.add_page()
    pdf.ln(15)
    y = pdf.get_y()
    pdf.line(pdf.l_margin, y, pdf.l_margin + 80, y)
    pdf.set_font(pdf.font_name, "", 8)
    pdf.cell(0, 5, "Datum, Unterschrift Auftraggeber")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output_path))
    return output_path
