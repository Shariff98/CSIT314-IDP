"""Control: SearchCategoryController (US-59 View and search IDP categories)."""
from entity.category import Category


class SearchCategoryController:
    def search(self, keyword="", status=None):
        """Each result includes how many IDPs use the category."""
        status = status if status in ("Active", "Suspended") else None
        return [{"category": c, "idps": c.idp_count()} for c in Category.search((keyword or "").strip(), status)]

    def view(self, category_id):
        return Category.find_by_id(category_id)

    def active_names(self):
        """Used by designer and customer pages to fill category drop-downs."""
        return [c.name for c in Category.all_active()]
