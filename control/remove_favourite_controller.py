"""Control: RemoveFavouriteController (US-56 Remove IDP from favourites)."""
from entity.favourite import Favourite


class RemoveFavouriteController:
    def remove(self, customer_id, idp_id):
        """Returns 'removed' or 'not_saved'. The IDP's shortlist count drops by one."""
        return "removed" if Favourite.remove(customer_id, idp_id) else "not_saved"
