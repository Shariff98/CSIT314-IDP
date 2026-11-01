"""Control: DeleteIDPController (US-05 Delete IDP)."""
from control.ownership import own_idp


class DeleteIDPController:
    def delete(self, designer_id, idp_id):
        """Returns 'deleted' or 'not_found'. Its photos, favourites and views go with it."""
        try:
            idp = own_idp(designer_id, idp_id)
        except LookupError:
            return "not_found"
        idp.delete()
        return "deleted"
