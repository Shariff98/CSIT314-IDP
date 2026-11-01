"""Control: ViewFavouritesController (US-44 View favourites list)."""
from entity.favourite import Favourite


class ViewFavouritesController:
    def list_favourites(self, customer_id):
        """The customer's saved projects, most recently saved first."""
        return Favourite.list_for_customer(customer_id)
