"""Feature 6: platform management.
US-20 Top categories and IDPs, US-30 Monthly report, US-38 Update category, US-39 Daily report,
US-40 Export reports, US-49 Create category, US-50 Dashboard, US-60 Suspend or delete category."""
import pytest

from control.create_category_controller import CreateCategoryController
from control.export_report_controller import ExportReportController
from control.generate_daily_report_controller import GenerateDailyReportController
from control.generate_monthly_report_controller import GenerateMonthlyReportController
from control.platform_dashboard_controller import PlatformDashboardController
from control.suspend_category_controller import SuspendCategoryController
from control.update_category_controller import UpdateCategoryController
from control.view_top_categories_controller import ViewTopCategoriesController
from entity.category import Category
from entity.favourite import Favourite
from entity.idp import IDP


# ---------- US-49 Create category ----------
def test_create_category(app):
    category = CreateCategoryController().create_category("  Walk-in   Wardrobe ", "Dressing rooms")
    assert category.name == "Walk-in Wardrobe"
    assert category.status == "Active"


@pytest.mark.parametrize("name, message", [("kitchen", "already exists"), ("", "name"), ("x" * 41, "40")])
def test_create_category_rejects_bad_names(app, name, message):
    with pytest.raises(ValueError, match=message):
        CreateCategoryController().create_category(name, "")


# ---------- US-38 Update category ----------
def test_rename_category_moves_its_projects(make_idp):
    idp = make_idp(category="Office")
    office = Category.find_by_name("Office")
    UpdateCategoryController().update_category(office.id, "Home Office", "Study rooms")
    assert IDP.find_by_id(idp.id).category == "Home Office"
    assert Category.find_by_id(office.id).description == "Study rooms"


def test_rename_to_existing_name_is_rejected(app):
    with pytest.raises(ValueError, match="already exists"):
        UpdateCategoryController().update_category(Category.find_by_name("Office").id, "Kitchen", "")


def test_update_unknown_category(app):
    with pytest.raises(LookupError):
        UpdateCategoryController().update_category(999, "X", "")


# ---------- US-60 Suspend or delete category and reassign IDPs ----------
def test_suspend_empty_category(app):
    office = Category.find_by_name("Office")
    assert SuspendCategoryController().suspend(office.id) == 0
    assert Category.find_by_id(office.id).status == "Suspended"


def test_suspend_category_with_projects_needs_reassign_target(make_idp):
    make_idp(category="Office")
    office = Category.find_by_name("Office")
    with pytest.raises(ValueError, match="choose another active category"):
        SuspendCategoryController().suspend(office.id)
    assert SuspendCategoryController().suspend(office.id, "Kitchen") == 1
    assert [i.category for i in IDP.filter()] == ["Kitchen"]


def test_cannot_reassign_to_same_or_suspended_category(make_idp):
    make_idp(category="Office")
    Category.find_by_name("Bathroom").suspend()
    office = Category.find_by_name("Office")
    for target in ("Office", "Bathroom", "Nowhere"):
        with pytest.raises(ValueError):
            SuspendCategoryController().suspend(office.id, target)


def test_delete_category_reassigns_then_deletes(make_idp):
    idp = make_idp(category="Office")
    office = Category.find_by_name("Office")
    assert SuspendCategoryController().delete(office.id, "Bedroom") == 1
    assert Category.find_by_id(office.id) is None
    assert IDP.find_by_id(idp.id).category == "Bedroom"


def test_reactivate_category(app):
    office = Category.find_by_name("Office")
    controller = SuspendCategoryController()
    controller.suspend(office.id)
    assert controller.reactivate(office.id).status == "Active"


def test_last_active_category_cannot_be_removed(app):
    controller = SuspendCategoryController()
    for c in Category.all_active()[:-1]:
        controller.suspend(c.id)
    last = Category.all_active()[0]
    with pytest.raises(ValueError, match="At least one"):
        controller.delete(last.id)


# ---------- US-39 Daily report ----------
def test_daily_report_counts_one_day(make_idp, customer):
    idp = make_idp(created_at="2026-03-02 09:00:00")
    idp.record_view(viewed_at="2026-03-02 23:59:59")
    idp.record_view(viewed_at="2026-03-03 00:00:00")
    Favourite.add(customer.id, idp.id, saved_at="2026-03-02 12:00:00")
    report = GenerateDailyReportController().generate("2026-03-02")
    assert (report.start, report.end) == ("2026-03-02", "2026-03-02")
    assert report.metrics["New IDPs"] == 1
    assert report.metrics["IDP views"] == 1
    assert report.metrics["Shortlists (saved to favourites)"] == 1
    assert report.previous.start == "2026-03-01"


# ---------- US-30 Monthly report ----------
def test_monthly_report_covers_whole_month(make_idp):
    idp = make_idp(created_at="2026-02-01 00:00:00")
    make_idp(created_at="2026-02-28 23:00:00")
    make_idp(created_at="2026-03-01 00:00:00")
    idp.record_view(viewed_at="2026-01-31 12:00:00")
    report = GenerateMonthlyReportController().generate("2026-02-15")
    assert (report.start, report.end) == ("2026-02-01", "2026-02-28")
    assert report.metrics["New IDPs"] == 2
    assert report.previous.start == "2026-01-01"
    assert report.previous.metrics["IDP views"] == 1


def test_monthly_report_handles_leap_year(app):
    report = GenerateMonthlyReportController().generate("2024-02-10")
    assert report.end == "2024-02-29"


# ---------- US-40 Export reports ----------
def test_export_csv_report(make_idp):
    make_idp(created_at="2026-03-02 09:00:00")
    name, mime, data = ExportReportController().export("weekly", "2026-03-04", "csv")
    assert name == "weekly-report-2026-03-02.csv" and mime == "text/csv"
    assert b"New IDPs,1" in data


def test_export_pdf_report(app):
    name, mime, data = ExportReportController().export("monthly", "2026-03-04", "pdf")
    assert name.endswith(".pdf") and mime == "application/pdf"
    assert data.startswith(b"%PDF-1.4") and data.rstrip().endswith(b"%%EOF")
    assert b"Monthly Report" in data


@pytest.mark.parametrize("period, fmt", [("yearly", "csv"), ("daily", "xlsx")])
def test_export_rejects_unknown_period_or_format(app, period, fmt):
    with pytest.raises(ValueError):
        ExportReportController().export(period, None, fmt)


# ---------- US-50 Platform dashboard ----------
def test_dashboard_totals(designer, customer, make_idp):
    idp = make_idp()
    make_idp(published=False)
    idp.record_view()
    Favourite.add(customer.id, idp.id)
    customer.suspend()
    data = PlatformDashboardController().metrics()
    totals = data["totals"]
    assert totals["Active interior designers"] == 1
    assert totals["Active customers"] == 0
    assert (totals["Total IDPs"], totals["Published IDPs"]) == (2, 1)
    assert (totals["Total favourites"], totals["Total views"]) == (1, 1)
    assert data["today"].metrics["IDP views"] == 1


# ---------- US-20 Top categories and IDPs ----------
def test_top_categories_and_idps(make_idp, customer):
    kitchen = make_idp("Kitchen 1", category="Kitchen")
    bedroom = make_idp("Bedroom 1")
    for _ in range(3):
        kitchen.record_view()
    Favourite.add(customer.id, bedroom.id)
    data = ViewTopCategoriesController().view()
    assert data["categories"][0]["name"] == "Kitchen"
    assert data["most_viewed"][0]["title"] == "Kitchen 1"
    assert data["most_shortlisted"][0]["title"] == "Bedroom 1"
