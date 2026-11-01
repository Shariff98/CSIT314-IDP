"""Control: ViewTopCategoriesController (US-20 View top categories and top IDPs)."""
from entity.report import Report


class ViewTopCategoriesController:
    def view(self, limit=5):
        """What customers want: the busiest categories and the most viewed and most shortlisted IDPs."""
        return {"categories": Report.top_categories_overall(limit),
                "most_viewed": Report.top_idps_overall("views", limit),
                "most_shortlisted": Report.top_idps_overall("saves", limit)}
