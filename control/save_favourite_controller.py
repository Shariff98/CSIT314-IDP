"""Control: SaveFavouriteController (US-19 Save IDP to favourites)."""
from control.notify_milestone_controller import NotifyMilestoneController
from entity.favourite import Favourite
from entity.idp import IDP


class SaveFavouriteController:
    def save(self, customer_id, idp_id):
        """Returns 'saved', 'already_saved' or 'not_found'. Saving also counts as one shortlist."""
        idp = IDP.find_by_id(idp_id)
        if idp is None or not idp.is_published:
            return "not_found"
        if not Favourite.add(customer_id, idp_id):
            return "already_saved"
        NotifyMilestoneController().check(idp)
        return "saved"

    def is_saved(self, customer_id, idp_id):
        return customer_id is not None and Favourite.exists(customer_id, idp_id)

    def list_favourites(self, customer_id):
        return Favourite.list_for_customer(customer_id)
