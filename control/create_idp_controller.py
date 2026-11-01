"""Control: CreateIDPController (US-54 Create interior design project)."""
from control.ownership import check_category, check_property_type, check_tags
from control.validation import clean, require, to_date, to_int
from entity.idp import IDP


def check_idp_details(title, description, category, budget, property_type, location, completion_date):
    """Rules shared by create (US-54) and update (US-04)."""
    require(title=title, description=description, category=category)
    budget = to_int(budget, "Budget", minimum=1)
    return dict(title=clean(title), description=clean(description), category=check_category(category),
                budget=budget, property_type=check_property_type(property_type), location=clean(location),
                completion_date=to_date(completion_date, "Completion date"))


class CreateIDPController:
    REQUIRED = ("title", "description", "category")

    def create_idp(self, designer_id, title, description, category, budget, property_type="", location="",
                   completion_date=None, style_tags="", publish=True):
        """Validates the input, then asks the IDP entity to save it.
        Raises ValueError with a message the boundary can show to the user.
        publish=False saves it as a draft that customers cannot see (US-33)."""
        details = check_idp_details(title, description, category, budget, property_type, location,
                                    completion_date)
        return IDP.create(designer_id, style_tags=check_tags(style_tags), published=publish, **details)
