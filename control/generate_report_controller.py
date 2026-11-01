"""Shared logic for the three report use cases (US-39 daily, US-10 weekly, US-30 monthly).

Each report is compared with the period before it, so platform management can see the trend."""
from datetime import date

from control.validation import to_date
from entity.report import Report


class GenerateReportController:
    PERIOD = None

    def date_range(self, ref):
        """Returns (start, end) date objects of the period that contains ref. Subclasses define it."""
        raise NotImplementedError

    def previous(self, start):
        raise NotImplementedError

    def generate(self, ref_date=None):
        ref = date.fromisoformat(to_date(ref_date, "Report date") or date.today().isoformat())
        if ref > date.today():
            raise ValueError("Report date cannot be in the future")
        start, end = self.date_range(ref)
        prev_start, prev_end = self.date_range(self.previous(start))
        report = Report.build(self.PERIOD, start.isoformat(), end.isoformat())
        before = Report.build(self.PERIOD, prev_start.isoformat(), prev_end.isoformat())
        report.previous = before
        report.changes = {name: value - before.metrics[name] for name, value in report.metrics.items()}
        return report
