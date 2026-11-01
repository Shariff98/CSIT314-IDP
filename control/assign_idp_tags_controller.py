"""Control: AssignIDPTagsController (US-26 Assign category and style tags to IDP)."""
from control.ownership import check_category, check_tags, own_idp


class AssignIDPTagsController:
    def assign(self, designer_id, idp_id, category, style_tags):
        idp = own_idp(designer_id, idp_id)
        idp.update(category=check_category(category), style_tags=check_tags(style_tags))
        return idp
