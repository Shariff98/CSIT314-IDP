"""Control: FilterIDPController (US-17 Filter IDPs by category, style, budget, type and location)."""
from control.browse_idp_controller import check_sort
from control.validation import clean, to_int
from entity.idp import IDP


class FilterIDPController:
    def filter(self, keyword="", category=None, style=None, min_budget=None, max_budget=None,
               property_type=None, location=None, sort="newest"):
        """Blank filters are ignored, so customers can combine any of them."""
        low = to_int(min_budget, "Minimum budget", minimum=0, allow_blank=True)
        high = to_int(max_budget, "Maximum budget", minimum=0, allow_blank=True)
        if low is not None and high is not None and low > high:
            raise ValueError("Minimum budget cannot be more than maximum budget")
        return IDP.filter(keyword=clean(keyword), category=clean(category) or None, style=clean(style) or None,
                          min_budget=low, max_budget=high, property_type=clean(property_type) or None,
                          location=clean(location) or None, sort=check_sort(sort))
