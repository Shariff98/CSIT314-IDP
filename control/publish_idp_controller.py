"""Control: PublishIDPController (US-33 Save IDP as draft, publish and unpublish)."""
from control.ownership import check_category, own_idp


class PublishIDPController:
    def publish(self, designer_id, idp_id):
        """Returns 'published' or 'already_published'. Raises if it can't be shown to customers yet."""
        idp = own_idp(designer_id, idp_id)
        if idp.is_published:
            return "already_published"
        check_category(idp.category)
        idp.update(published=1)
        return "published"

    def unpublish(self, designer_id, idp_id):
        """Returns 'unpublished' or 'already_draft'. Customers stop seeing it straight away."""
        idp = own_idp(designer_id, idp_id)
        if not idp.is_published:
            return "already_draft"
        idp.update(published=0)
        return "unpublished"
