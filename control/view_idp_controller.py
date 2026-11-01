"""Control: ViewIDPController (US-34 View IDP details, US-37 Count repeat views once per session)."""
from control.notify_milestone_controller import NotifyMilestoneController
from entity.idp import IDP


class ViewIDPController:
    def view(self, idp_id, viewer_id=None, session_key=None):
        """Returns the IDP, or None if it doesn't exist or is a draft the viewer doesn't own.
        Each view adds one to the view count, except:
          - the designer looking at their own project, and
          - the same browser session looking at the same project again (US-37)."""
        idp = IDP.find_by_id(idp_id)
        if idp is None:
            return None
        is_owner = viewer_id is not None and viewer_id == idp.designer_id
        if not idp.is_published and not is_owner:
            return None
        if not is_owner and not (session_key and idp.seen_in_session(session_key)):
            idp.record_view(customer_id=viewer_id, session_key=session_key)
            NotifyMilestoneController().check(idp)
        return idp
