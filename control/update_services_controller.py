"""Control: UpdateServicesController (US-14 State budget range and services offered)."""
from control.update_company_info_controller import company_for
from control.validation import clean_list, to_int


class UpdateServicesController:
    def update(self, designer_id, budget_min, budget_max, services):
        low = to_int(budget_min, "Minimum budget", minimum=1)
        high = to_int(budget_max, "Maximum budget", minimum=1)
        if low > high:
            raise ValueError("Minimum budget cannot be more than maximum budget")
        services = clean_list(services)
        if not services:
            raise ValueError("Add at least one service, e.g. Full renovation")
        company = company_for(designer_id)
        company.save(budget_min=low, budget_max=high, services=services)
        return company
