"""Control: RankIDPsController (US-09 Rank IDPs by views or shortlists)."""
from entity.idp import IDP

METRICS = ("views", "shortlists")


class RankIDPsController:
    def rank(self, designer_id, metric="views"):
        """Ranks the designer's projects. Ties share a rank (1, 2, 2, 4 ...)."""
        if metric not in METRICS:
            raise ValueError("Rank by views or shortlists")
        rows = [{"idp": i, "views": i.views, "shortlists": i.shortlist_count()}
                for i in IDP.list_for_designer(designer_id)]
        rows.sort(key=lambda r: (-r[metric], r["idp"].title))
        previous, rank = None, 0
        for position, row in enumerate(rows, start=1):
            if row[metric] != previous:
                rank, previous = position, row[metric]
            row["rank"] = rank
        return rows
