"""Control: ViewMyIDPController (US-27 View my IDP details)."""
from control.ownership import own_idp


class ViewMyIDPController:
    def view(self, designer_id, idp_id):
        """The designer's own project, drafts included. Does not count as a customer view."""
        try:
            return own_idp(designer_id, idp_id)
        except LookupError:
            return None
