"""Control: UpdateCredentialsController (US-12 Add certifications, awards and experience)."""
from control.update_company_info_controller import company_for
from control.validation import clean_list, to_int


class UpdateCredentialsController:
    def update(self, designer_id, certifications, awards, years_experience):
        years = to_int(years_experience, "Years of experience", minimum=0, maximum=80)
        company = company_for(designer_id)
        company.save(certifications=clean_list(certifications), awards=clean_list(awards), years_experience=years)
        return company
