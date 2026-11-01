"""Feature 5: interest tracking for designers.
US-09 Rank, US-29 View count, US-35 Date range, US-36 Segment filter, US-47 CSV export,
US-48 Milestone notifications, US-57 Dashboard, US-58 Compare."""
import csv
import io
from datetime import date, timedelta

import pytest

from control.compare_idps_controller import CompareIDPsController
from control.export_interest_csv_controller import ExportInterestCSVController
from control.filter_analytics_controller import FilterAnalyticsController
from control.notify_milestone_controller import NotifyMilestoneController
from control.portfolio_dashboard_controller import PortfolioDashboardController
from control.rank_idps_controller import RankIDPsController
from control.save_favourite_controller import SaveFavouriteController
from control.view_idp_controller import ViewIDPController
from control.view_idp_view_count_controller import ViewIDPViewCountController
from control.view_interest_by_date_range_controller import ViewInterestByDateRangeController
from entity.favourite import Favourite
from entity.user_account import UserAccount


def views(idp, n, day=None):
    for _ in range(n):
        idp.record_view(viewed_at=day)


def customers(n):
    return [UserAccount.create(f"C{i}", f"c{i}@example.com", "pass123", "Customer") for i in range(n)]


# ---------- US-29 View IDP view count ----------
def test_view_counts_per_project_and_total(designer, make_idp):
    a, b = make_idp("A"), make_idp("B")
    views(a, 3)
    views(b, 1)
    data = ViewIDPViewCountController().view_counts(designer.id)
    assert {r["idp"].title: r["views"] for r in data["rows"]} == {"A": 3, "B": 1}
    assert data["total"] == 4


# ---------- US-09 Rank IDPs ----------
def test_rank_by_views_with_ties(designer, make_idp):
    a, b, c = make_idp("A"), make_idp("B"), make_idp("C")
    views(a, 5)
    views(b, 5)
    views(c, 1)
    rows = RankIDPsController().rank(designer.id, "views")
    assert [(r["rank"], r["idp"].title) for r in rows] == [(1, "A"), (1, "B"), (3, "C")]


def test_rank_by_shortlists(designer, make_idp):
    a, b = make_idp("A"), make_idp("B")
    Favourite.add(customers(1)[0].id, b.id)
    assert RankIDPsController().rank(designer.id, "shortlists")[0]["idp"].title == "B"


def test_rank_rejects_unknown_metric(designer):
    with pytest.raises(ValueError):
        RankIDPsController().rank(designer.id, "likes")


# ---------- US-35 Views and shortlists by date range ----------
def test_daily_trend_includes_empty_days(designer, make_idp, customer):
    idp = make_idp()
    views(idp, 2, "2026-03-02 10:00:00")
    views(idp, 1, "2026-03-04 10:00:00")
    Favourite.add(customer.id, idp.id, saved_at="2026-03-04 11:00:00")
    data = ViewInterestByDateRangeController().trend(designer.id, "daily", "2026-03-01", "2026-03-04")
    assert [(r["label"], r["views"], r["shortlists"]) for r in data["rows"]] == [
        ("2026-03-01", 0, 0), ("2026-03-02", 2, 0), ("2026-03-03", 0, 0), ("2026-03-04", 1, 1)]
    assert (data["total_views"], data["total_shortlists"]) == (3, 1)


def test_weekly_and_monthly_grouping(designer, make_idp):
    idp = make_idp()
    views(idp, 1, "2026-03-02 10:00:00")     # Monday
    views(idp, 1, "2026-03-08 10:00:00")     # Sunday, same week
    views(idp, 1, "2026-04-01 10:00:00")
    weekly = ViewInterestByDateRangeController().trend(designer.id, "weekly", "2026-03-02", "2026-03-15")
    assert [(r["label"], r["views"]) for r in weekly["rows"]] == [("2026-03-02", 2), ("2026-03-09", 0)]
    monthly = ViewInterestByDateRangeController().trend(designer.id, "monthly", "2026-03-01", "2026-04-30")
    assert [(r["label"], r["views"]) for r in monthly["rows"]] == [("2026-03", 2), ("2026-04", 1)]


def test_other_designers_views_are_excluded(designer, other_designer, make_idp):
    views(make_idp(designer_id=other_designer.id), 4, "2026-03-02 10:00:00")
    data = ViewInterestByDateRangeController().trend(designer.id, "daily", "2026-03-02", "2026-03-02")
    assert data["total_views"] == 0


@pytest.mark.parametrize("period, start, end, message", [("hourly", None, None, "Period"),
                                                         ("daily", "2026-03-05", "2026-03-01", "Start date"),
                                                         ("daily", "2024-01-01", "2026-01-01", "one year")])
def test_trend_rejects_bad_ranges(designer, period, start, end, message):
    with pytest.raises(ValueError, match=message):
        ViewInterestByDateRangeController().trend(designer.id, period, start, end)


def test_default_range_ends_today(designer):
    data = ViewInterestByDateRangeController().trend(designer.id)
    assert data["end"] == date.today().isoformat()
    assert len(data["rows"]) == 14


# ---------- US-36 Filter analytics by category or status ----------
def test_segment_by_category_and_status(designer, make_idp, customer):
    kitchen = make_idp("Kitchen", category="Kitchen", status="Past")
    make_idp("Bedroom")
    views(kitchen, 4)
    Favourite.add(customer.id, kitchen.id)
    data = FilterAnalyticsController().filter(designer.id, category="Kitchen", status="Past")
    assert (data["projects"], data["views"], data["shortlists"], data["save_rate"]) == (1, 4, 1, 25.0)
    assert FilterAnalyticsController().filter(designer.id, category="Office")["projects"] == 0


# ---------- US-57 Portfolio dashboard ----------
def test_dashboard_summary(designer, make_idp, customer):
    top = make_idp("Top")
    make_idp("Draft", published=False)
    views(top, 10)
    Favourite.add(customer.id, top.id)
    summary = PortfolioDashboardController().summary(designer.id)
    assert (summary["projects"], summary["published"], summary["drafts"]) == (2, 1, 1)
    assert (summary["views"], summary["shortlists"], summary["save_rate"]) == (10, 1, 10.0)
    assert summary["views_30_days"] == 10
    assert summary["top_project"].title == "Top"


def test_dashboard_with_no_projects(designer):
    summary = PortfolioDashboardController().summary(designer.id)
    assert summary["projects"] == 0 and summary["top_project"] is None and summary["save_rate"] == 0.0


# ---------- US-58 Compare IDP performance ----------
def test_compare_projects_and_pick_best(designer, make_idp, customer):
    a, b = make_idp("A"), make_idp("B")
    views(a, 10)
    views(b, 2)
    Favourite.add(customer.id, b.id)
    result = CompareIDPsController().compare(designer.id, [a.id, str(b.id)])
    assert [r["save_rate"] for r in result["rows"]] == [0.0, 50.0]
    assert result["best"].title == "B"


@pytest.mark.parametrize("count", [1, 5])
def test_compare_needs_two_to_four(designer, make_idp, count):
    ids = [make_idp(f"P{i}").id for i in range(count)]
    with pytest.raises(ValueError, match="between 2 and 4"):
        CompareIDPsController().compare(designer.id, ids)


def test_cannot_compare_another_designers_project(designer, other_designer, make_idp):
    with pytest.raises(LookupError):
        CompareIDPsController().compare(designer.id, [make_idp().id, make_idp(designer_id=other_designer.id).id])


# ---------- US-47 Export interest statistics as CSV ----------
def test_export_csv(designer, make_idp):
    idp = make_idp("Loft, with comma")
    views(idp, 2)
    rows = list(csv.reader(io.StringIO(ExportInterestCSVController().export(designer.id))))
    assert rows[0] == ExportInterestCSVController.HEADER
    assert rows[1][1] == "Loft, with comma"
    assert rows[1][-2:] == ["2", "0"]


# ---------- US-48 Milestone notifications ----------
def test_notification_when_view_milestone_reached(designer, make_idp):
    idp = make_idp("Loft")
    for i in range(10):
        ViewIDPController().view(idp.id, session_key=f"s{i}")
    notes = NotifyMilestoneController().list_notifications(designer.id)
    assert [n.message for n in notes] == ["'Loft' reached 10 views"]


def test_milestone_notified_only_once(designer, make_idp):
    idp = make_idp("Loft")
    views(idp, 10)
    controller = NotifyMilestoneController()
    assert len(controller.check(idp)) == 1
    assert controller.check(idp) == []


def test_notification_when_shortlist_milestone_reached(designer, make_idp):
    idp = make_idp("Loft")
    for c in customers(5):
        SaveFavouriteController().save(c.id, idp.id)
    controller = NotifyMilestoneController()
    assert controller.unread_count(designer.id) == 1
    controller.mark_all_read(designer.id)
    assert controller.unread_count(designer.id) == 0
