"""Control: SearchIDPController (US-28 Search IDPs by keyword)."""
from control.browse_idp_controller import check_sort
from entity.idp import IDP


class SearchIDPController:
    def search(self, keyword, sort="newest"):
        """Matches title, description, style tags and location of published projects."""
        return IDP.search((keyword or "").strip(), sort=check_sort(sort))
