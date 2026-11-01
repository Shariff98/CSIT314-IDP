"""Control: ViewInterestByDateRangeController (US-35 View views and shortlists by date range)."""
from datetime import date, timedelta

from control.validation import to_date
from entity.idp import IDP

DEFAULT_DAYS = {"daily": 13, "weekly": 7 * 8 - 1, "monthly": 182}
MAX_DAYS = 366


def bucket(day, period):
    """The label a day is grouped under: the day, the Monday of its week, or its month."""
    if period == "weekly":
        return (day - timedelta(days=day.weekday())).isoformat()
    if period == "monthly":
        return day.strftime("%Y-%m")
    return day.isoformat()


class ViewInterestByDateRangeController:
    def trend(self, designer_id, period="daily", start=None, end=None, category=None, status=None, idp_ids=None):
        """Views and shortlists of the designer's projects grouped by day, week or month.
        Every bucket in the range is returned, including empty ones, so a chart has no gaps."""
        if period not in DEFAULT_DAYS:
            raise ValueError("Period must be daily, weekly or monthly")
        end = date.fromisoformat(to_date(end, "End date") or date.today().isoformat())
        start = date.fromisoformat(to_date(start, "Start date") or
                                   (end - timedelta(days=DEFAULT_DAYS[period])).isoformat())
        if start > end:
            raise ValueError("Start date must be on or before end date")
        if (end - start).days > MAX_DAYS:
            raise ValueError("Choose a range of one year or less")
        per_day = IDP.interest_by_day(designer_id, start.isoformat(), end.isoformat(), category, status, idp_ids)
        buckets = {}
        day = start
        while day <= end:
            entry = buckets.setdefault(bucket(day, period), {"label": bucket(day, period), "views": 0, "shortlists": 0})
            views, shortlists = per_day.get(day.isoformat(), (0, 0))
            entry["views"] += views
            entry["shortlists"] += shortlists
            day += timedelta(days=1)
        rows = list(buckets.values())
        return {"period": period, "start": start.isoformat(), "end": end.isoformat(), "rows": rows,
                "total_views": sum(r["views"] for r in rows), "total_shortlists": sum(r["shortlists"] for r in rows)}
