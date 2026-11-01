"""Control: MarkIDPStatusController (US-06 Mark IDP as current or past)."""
from datetime import date

from control.ownership import own_idp

STATUSES = ("Current", "Past")


class MarkIDPStatusController:
    def mark(self, designer_id, idp_id, status):
        if status not in STATUSES:
            raise ValueError("Status must be Current or Past")
        idp = own_idp(designer_id, idp_id)
        changes = {"status": status}
        if status == "Past" and not idp.completion_date:
            changes["completion_date"] = date.today().isoformat()   # a past project must have an end date
        idp.update(**changes)
        return idp
