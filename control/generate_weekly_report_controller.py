"""Control: GenerateWeeklyReportController (US-10 Generate weekly report)."""
from datetime import timedelta

from control.generate_report_controller import GenerateReportController


class GenerateWeeklyReportController(GenerateReportController):
    PERIOD = "Weekly"

    def date_range(self, ref):
        """Monday to Sunday of the week that contains ref."""
        monday = ref - timedelta(days=ref.weekday())
        return monday, monday + timedelta(days=6)

    def previous(self, start):
        return start - timedelta(days=7)
