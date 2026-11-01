"""Control: UpdateCompanyInfoController (US-32 Update company information)."""
from control.create_company_profile_controller import check_company_details
from control.validation import clean
from entity.company import Company


def company_for(designer_id):
    company = Company.find_by_designer(designer_id)
    if company is None:
        raise LookupError("Create your company profile first")
    return company


class UpdateCompanyInfoController:
    def update_company(self, designer_id, name, registration_no, address, phone, email, description):
        company = company_for(designer_id)
        name, registration_no, address, phone, email = check_company_details(
            name, registration_no, address, phone, email, except_id=company.id)
        company.save(name=name, registration_no=registration_no, address=address, phone=phone,
                     email=email, description=clean(description))
        return company
