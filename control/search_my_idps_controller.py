"""Control: SearchMyIDPsController (US-03 Search and filter my IDPs)."""
from control.validation import to_date
from entity.idp import IDP

STATUS_FILTERS = ("Current", "Past", "Draft", "Published")


class SearchMyIDPsController:
    def search(self, designer_id, keyword="", status=None, category=None, date_from=None, date_to=None):
        """Searches only the designer's own projects by keyword, status, category and created date."""
        if status and status not in STATUS_FILTERS:
            raise ValueError("Unknown status filter")
        date_from = to_date(date_from, "From date")
        date_to = to_date(date_to, "To date")
        if date_from and date_to and date_from > date_to:
            raise ValueError("From date must be on or before To date")
        return IDP.list_for_designer(designer_id, keyword=(keyword or "").strip(), status=status or None,
                                     category=category or None, date_from=date_from, date_to=date_to)
