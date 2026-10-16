from site_report_bot.models import MaterialItem, SiteReport


def test_minimal_report():
    report = SiteReport(summary="Trockenbau im EG abgeschlossen.")
    assert report.materials == []
    assert report.report_date is not None


def test_material_optional_fields():
    item = MaterialItem(name="Schrauben")
    assert item.quantity is None