"""Control: FilterAnalyticsController (US-36 Filter analytics by category or status)."""
from entity.idp import IDP


class FilterAnalyticsController:
    def filter(self, designer_id, category=None, status=None):
        """Interest statistics for one segment of the portfolio, e.g. only past Kitchen projects."""
        if status and status not in ("Current", "Past", "Draft", "Published"):
            raise ValueError("Unknown status filter")
        idps = IDP.list_for_designer(designer_id, status=status or None, category=category or None, sort="views")
        rows = [{"idp": i, "views": i.views, "shortlists": i.shortlist_count()} for i in idps]
        views = sum(r["views"] for r in rows)
        shortlists = sum(r["shortlists"] for r in rows)
        return {"rows": rows, "projects": len(rows), "views": views, "shortlists": shortlists,
                "save_rate": round(100 * shortlists / views, 1) if views else 0.0}
