"""Control: PortfolioDashboardController (US-57 View portfolio analytics dashboard)."""
from datetime import date, timedelta

from entity.idp import IDP


class PortfolioDashboardController:
    def summary(self, designer_id):
        idps = IDP.list_for_designer(designer_id)
        counts = [(i, i.views, i.shortlist_count()) for i in idps]
        views = sum(v for _, v, _ in counts)
        shortlists = sum(s for _, _, s in counts)
        today = date.today()
        recent = IDP.interest_by_day(designer_id, (today - timedelta(days=29)).isoformat(), today.isoformat())
        top = max(counts, key=lambda c: (c[1], c[2]), default=None)
        return {
            "projects": len(idps),
            "published": sum(1 for i in idps if i.is_published),
            "drafts": sum(1 for i in idps if not i.is_published),
            "views": views,
            "shortlists": shortlists,
            "save_rate": round(100 * shortlists / views, 1) if views else 0.0,
            "views_30_days": sum(v for v, _ in recent.values()),
            "shortlists_30_days": sum(s for _, s in recent.values()),
            "top_project": top[0] if top else None,
        }
