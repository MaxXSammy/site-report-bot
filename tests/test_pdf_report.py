from site_report_bot.models import LaborEntry, MaterialItem, SiteReport
from site_report_bot.pdf_report import _fmt_number, create_pdf


def test_create_pdf(tmp_path):
    report = SiteReport(
        project_name="Baustelle Test",
        summary="Testbericht mit Umlauten: äöüß",
        materials=[MaterialItem(name="Schrauben", quantity=100, unit="Stück")],
        labor=[LaborEntry(worker="Geselle", hours=7.5)],
        remarks=["Abnahme durch Kunden erfolgt"],
    )
    path = create_pdf(report, tmp_path / "bericht.pdf")
    assert path.exists()
    assert path.read_bytes().startswith(b"%PDF")


def test_fmt_number():
    assert _fmt_number(6.0) == "6"
    assert _fmt_number(2.5) == "2,5"
    assert _fmt_number(None) == ""
