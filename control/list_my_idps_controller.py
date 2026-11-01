"""Control: ListMyIDPsController (US-16 View list of my IDPs)."""
from entity.idp import IDP


class ListMyIDPsController:
    def list_idps(self, designer_id, sort="newest"):
        """All of the designer's projects, drafts included."""
        return IDP.list_for_designer(designer_id, sort=sort)
