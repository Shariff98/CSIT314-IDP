"""Control: PlatformDashboardController (US-50 View platform key metrics dashboard)."""
from control.generate_daily_report_controller import GenerateDailyReportController
from entity.report import Report


class PlatformDashboardController:
    def metrics(self):
        """Platform health at a glance: overall totals plus today's activity."""
        return {"totals": Report.platform_totals(), "today": GenerateDailyReportController().generate()}
