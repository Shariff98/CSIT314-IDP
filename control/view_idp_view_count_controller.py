"""Control: ViewIDPViewCountController (US-29 View IDP view count)."""
from entity.idp import IDP


class ViewIDPViewCountController:
    def view_counts(self, designer_id):
        """Each of the designer's projects with its number of views, and the total."""
        rows = [{"idp": idp, "views": idp.views} for idp in IDP.list_for_designer(designer_id)]
        return {"rows": rows, "total": sum(r["views"] for r in rows)}
