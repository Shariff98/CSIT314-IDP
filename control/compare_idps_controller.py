"""Control: CompareIDPsController (US-58 Compare IDP performance)."""
from datetime import date, timedelta

from control.ownership import own_idp
from entity.idp import IDP


class CompareIDPsController:
    def compare(self, designer_id, idp_ids):
        """Side-by-side figures for 2 to 4 of the designer's own projects."""
        ids = list(dict.fromkeys(int(i) for i in idp_ids))
        if not 2 <= len(ids) <= 4:
            raise ValueError("Choose between 2 and 4 projects to compare")
        idps = [own_idp(designer_id, i) for i in ids]
        today = date.today()
        rows = []
        for idp in idps:
            recent = IDP.interest_by_day(designer_id, (today - timedelta(days=29)).isoformat(), today.isoformat(),
                                         idp_ids=[idp.id])
            shortlists = idp.shortlist_count()
            rows.append({"idp": idp, "views": idp.views, "shortlists": shortlists,
                         "save_rate": round(100 * shortlists / idp.views, 1) if idp.views else 0.0,
                         "views_30_days": sum(v for v, _ in recent.values())})
        best = max(rows, key=lambda r: (r["save_rate"], r["views"]))
        return {"rows": rows, "best": best["idp"]}
