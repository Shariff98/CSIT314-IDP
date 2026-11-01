"""US-10 Generate weekly report."""
from datetime import date, timedelta

import pytest

from control.generate_weekly_report_controller import GenerateWeeklyReportController
from entity.favourite import Favourite
from entity.user_account import UserAccount


@pytest.fixture
def activity(make_idp, customer):
    # Week of Mon 2 Mar - Sun 8 Mar 2026, and the week before it.
    kitchen = make_idp("Kitchen A", category="Kitchen", created_at="2026-03-03 09:00:00")
    make_idp("Old Bedroom", created_at="2026-02-25 09:00:00")
    UserAccount.create("New Customer", "new@example.com", "pass12345", "Customer", created_at="2026-03-08 23:59:00")
    for day in ("2026-03-02 08:00:00", "2026-03-04 12:00:00", "2026-03-09 00:00:01"):
        kitchen.record_view(viewed_at=day)
    Favourite.add(customer.id, kitchen.id, saved_at="2026-03-05 10:00:00")
    return kitchen


def test_week_runs_monday_to_sunday():
    start, end = GenerateWeeklyReportController().date_range(date(2026, 3, 5))
    assert (start.isoformat(), end.isoformat()) == ("2026-03-02", "2026-03-08")


def test_weekly_report_counts_only_that_week(activity):
    report = GenerateWeeklyReportController().generate("2026-03-05")
    assert report.metrics["New IDPs"] == 1
    assert report.metrics["New customers"] == 1
    assert report.metrics["IDP views"] == 2              # the view on 9 March belongs to next week
    assert report.metrics["Shortlists (saved to favourites)"] == 1
    assert report.top_idps[0]["title"] == "Kitchen A"
    assert report.top_categories[0] == {"name": "Kitchen", "views": 2}


def test_weekly_report_compares_with_previous_week(activity):
    report = GenerateWeeklyReportController().generate("2026-03-05")
    assert report.previous.start == "2026-02-23"
    assert report.previous.metrics["New IDPs"] == 1
    assert report.changes["New IDPs"] == 0
    assert report.changes["IDP views"] == 2


def test_empty_week_has_zero_counts(app):
    report = GenerateWeeklyReportController().generate("2025-01-01")
    assert set(report.metrics.values()) == {0}
    assert report.top_idps == []


def test_rejects_future_date(app):
    with pytest.raises(ValueError, match="future"):
        GenerateWeeklyReportController().generate((date.today() + timedelta(days=8)).isoformat())


def test_rejects_bad_date(app):
    with pytest.raises(ValueError, match="date"):
        GenerateWeeklyReportController().generate("next week")
