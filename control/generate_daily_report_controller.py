"""Control: GenerateDailyReportController (US-39 Generate daily report)."""
from datetime import timedelta

from control.generate_report_controller import GenerateReportController


class GenerateDailyReportController(GenerateReportController):
    PERIOD = "Daily"

    def date_range(self, ref):
        return ref, ref

    def previous(self, start):
        return start - timedelta(days=1)
