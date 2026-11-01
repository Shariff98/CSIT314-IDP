"""Control: UpdateSpecialisationsController (US-25 List design specialisations and service areas)."""
from control.update_company_info_controller import company_for
from control.validation import clean_list


class UpdateSpecialisationsController:
    def update(self, designer_id, specialisations, service_areas):
        specialisations, service_areas = clean_list(specialisations), clean_list(service_areas)
        if not specialisations:
            raise ValueError("Add at least one specialisation, e.g. Modern")
        if not service_areas:
            raise ValueError("Add at least one service area, e.g. Central")
        company = company_for(designer_id)
        company.save(specialisations=specialisations, service_areas=service_areas)
        return company
