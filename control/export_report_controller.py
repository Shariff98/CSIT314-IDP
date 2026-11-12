"""Control: ExportReportController (US-40 Export reports as PDF or CSV)."""
import csv
import io

from control.generate_daily_report_controller import GenerateDailyReportController
from control.generate_monthly_report_controller import GenerateMonthlyReportController
from control.generate_weekly_report_controller import GenerateWeeklyReportController
from control.pdf_writer import simple_pdf

GENERATORS = {"daily": GenerateDailyReportController, "weekly": GenerateWeeklyReportController,
              "monthly": GenerateMonthlyReportController}


class ExportReportController:
    def export(self, period, ref_date=None, file_format="csv"):
        """Returns (filename, mime type, bytes)."""
        if period not in GENERATORS:
            raise ValueError("Period must be daily, weekly or monthly")
        if file_format not in ("csv", "pdf"):
            raise ValueError("Format must be CSV or PDF")
        report = GENERATORS[period]().generate(ref_date)
        name = f"{period}-report-{report.start}.{file_format}"
        if file_format == "csv":
            out = io.StringIO()
            csv.writer(out).writerows(report.to_rows())
            return name, "text/csv", out.getvalue().encode("utf-8")
        lines = [" : ".join(str(cell) for cell in row) for row in report.to_rows()]
        return name, "application/pdf", simple_pdf(f"RenovationLink {report.period} Report", lines)
