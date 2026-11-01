"""Control: ExportInterestCSVController (US-47 Export interest statistics as CSV)."""
import csv
import io

from entity.idp import IDP


class ExportInterestCSVController:
    HEADER = ["IDP ID", "Title", "Category", "Status", "Published", "Created", "Views", "Shortlists"]

    def export(self, designer_id):
        """Returns the CSV text for all of the designer's projects."""
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(self.HEADER)
        for idp in IDP.list_for_designer(designer_id):
            writer.writerow([idp.id, idp.title, idp.category, idp.status, "Yes" if idp.is_published else "No",
                             (idp.created_at or "")[:10], idp.views, idp.shortlist_count()])
        return out.getvalue()
