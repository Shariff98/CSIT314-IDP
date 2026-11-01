"""Control: SearchFavouritesController (US-08 Search and filter favourites)."""
from entity.favourite import Favourite


class SearchFavouritesController:
    def search(self, customer_id, keyword="", category=None):
        """Only ever searches this customer's own favourites."""
        return Favourite.list_for_customer(customer_id, (keyword or "").strip(), category or None)
