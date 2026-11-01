"""Control: BrowseIDPController (US-07 Browse published IDPs, US-18 Sort IDPs)."""
from entity.idp import IDP

SORT_OPTIONS = {"newest": "Newest", "views": "Most viewed", "saves": "Most saved",
                "budget_low": "Budget: low to high", "budget_high": "Budget: high to low"}


def check_sort(sort):
    return sort if sort in SORT_OPTIONS else "newest"


class BrowseIDPController:
    def browse(self, sort="newest"):
        """Every published project, newest first unless another sort is chosen."""
        return IDP.filter(sort=check_sort(sort))
