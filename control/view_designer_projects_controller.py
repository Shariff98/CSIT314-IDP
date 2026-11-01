"""Control: ViewDesignerProjectsController (US-45 View other projects by same designer)."""
from entity.idp import IDP


class ViewDesignerProjectsController:
    def other_projects(self, idp_id, limit=6):
        """Other published projects by the designer of this IDP, most viewed first."""
        idp = IDP.find_by_id(idp_id)
        if idp is None:
            return []
        return IDP.filter(designer_id=idp.designer_id, exclude_id=idp.id, sort="views", limit=limit)
