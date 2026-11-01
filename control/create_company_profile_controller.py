"""Control: CreateCompanyProfileController (US-24 Create company profile)."""
import re

from control.validation import check_email, check_phone, clean, require
from entity.company import Company

REGISTRATION_NO = re.compile(r"^[A-Za-z0-9-]{5,20}$")


def check_company_details(name, registration_no, address, phone, email, except_id=None):
    """Rules shared by create (US-24) and update (US-32)."""
    require(company_name=name, registration_number=registration_no, address=address, email=email)
    registration_no = clean(registration_no).upper()
    if not REGISTRATION_NO.match(registration_no):
        raise ValueError("Registration number must be 5-20 letters, digits or dashes")
    if Company.registration_taken(registration_no, except_id):
        raise ValueError("This registration number is already registered")
    return clean(name), registration_no, clean(address), check_phone(phone), check_email(email)


class CreateCompanyProfileController:
    def create_company(self, designer_id, name, registration_no, address, phone, email, description):
        if Company.find_by_designer(designer_id) is not None:
            raise ValueError("You already have a company profile; update it instead")
        details = check_company_details(name, registration_no, address, phone, email)
        return Company.create(designer_id, *details, clean(description))
