"""Control: GenerateMonthlyReportController (US-30 Generate monthly report)."""
from calendar import monthrange
from datetime import timedelta

from control.generate_report_controller import GenerateReportController


class GenerateMonthlyReportController(GenerateReportController):
    PERIOD = "Monthly"

    def date_range(self, ref):
        first = ref.replace(day=1)
        return first, ref.replace(day=monthrange(ref.year, ref.month)[1])

    def previous(self, start):
        return start - timedelta(days=1)       # the last day of the month before
