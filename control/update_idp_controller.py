"""Control: UpdateIDPController (US-04 Update IDP)."""
from control.create_idp_controller import check_idp_details
from control.ownership import own_idp


class UpdateIDPController:
    def update_idp(self, designer_id, idp_id, title, description, category, budget, property_type="",
                   location="", completion_date=None):
        idp = own_idp(designer_id, idp_id)
        idp.update(**check_idp_details(title, description, category, budget, property_type, location,
                                       completion_date))
        return idp
