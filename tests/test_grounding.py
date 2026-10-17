from site_report_bot.grounding import fill_customer_from_project, remove_unsupported
from site_report_bot.models import LaborEntry, MaterialItem, ReportContent

NOTES = ["Bad Erdgeschoss, Fliesen an der Wand verlegt, Fugen fehlen noch"]


def report(**fields) -> ReportContent:
    return ReportContent(summary="Test", **fields)


def test_removes_invented_names():
    result = remove_unsupported(
        report(project_name="Baustelle Müller", customer_name="Müller"), NOTES
    )
    assert result.project_name == ""
    assert result.customer_name == ""


def test_keeps_names_from_notes():
    result = remove_unsupported(
        report(customer_name="Schmidt"), ["Bei Schmidt das Bad gefliest"]
    )
    assert result.customer_name == "Schmidt"


def test_removes_invented_quantity_but_keeps_material():
    material = MaterialItem(name="Fliesen", quantity=100, unit="Stück")
    result = remove_unsupported(report(materials=[material]), NOTES)
    assert result.materials[0].name == "Fliesen"
    assert result.materials[0].quantity is None


def test_removes_labor_with_invented_hours():
    result = remove_unsupported(
        report(labor=[LaborEntry(worker="Handwerker", hours=8)]), NOTES
    )
    assert result.labor == []


def test_keeps_spoken_numbers():
    entry = LaborEntry(worker="Geselle", hours=8)
    result = remove_unsupported(
        report(labor=[entry]), ["Geselle hat acht Stunden gearbeitet"]
    )
    assert len(result.labor) == 1


def test_customer_derived_from_project_name():
    result = fill_customer_from_project(report(project_name="Baustelle Schneider"))
    assert result.customer_name == "Schneider"


def test_existing_customer_is_kept():
    result = fill_customer_from_project(
        report(project_name="Baustelle Schneider", customer_name="Familie Weber")
    )
    assert result.customer_name == "Familie Weber"


def test_no_customer_from_plain_project_name():
    result = fill_customer_from_project(report(project_name="Neubau Kita"))
    assert result.customer_name == ""
