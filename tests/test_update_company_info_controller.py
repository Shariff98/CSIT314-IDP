"""US-32 Update company information."""
import pytest

from control.create_company_profile_controller import CreateCompanyProfileController
from control.update_company_info_controller import UpdateCompanyInfoController
from control.view_company_info_controller import ViewCompanyInfoController


@pytest.fixture
def company(designer):
    return CreateCompanyProfileController().create_company(
        designer.id, "Dana Interiors", "201912345K", "1 Main St", "+65 6123 4567", "hello@dana.sg", "We design homes")


def test_update_changes_the_stored_company(designer, company):
    UpdateCompanyInfoController().update_company(designer.id, "Dana Studio", "201912345k", "2 New Rd",
                                                 "6999 8888", "STUDIO@dana.sg", "Homes and offices")
    saved = ViewCompanyInfoController().view(designer.id)
    assert (saved.name, saved.address, saved.email) == ("Dana Studio", "2 New Rd", "studio@dana.sg")
    assert saved.registration_no == "201912345K"


def test_update_records_the_time(designer, company):
    before = company.updated_at
    updated = UpdateCompanyInfoController().update_company(designer.id, "Dana Studio", "201912345K", "1 Main St",
                                                           "", "hello@dana.sg", "")
    assert updated.updated_at >= before


@pytest.mark.parametrize("field, value, message", [
    ("name", " ", "company name"),
    ("registration_no", "12", "Registration number"),
    ("phone", "call me", "Phone"),
    ("email", "dana.sg", "Email"),
])
def test_rejects_invalid_details(designer, company, field, value, message):
    details = dict(name="Dana Studio", registration_no="201912345K", address="1 Main St", phone="",
                   email="hello@dana.sg", description="")
    details[field] = value
    with pytest.raises(ValueError, match=message):
        UpdateCompanyInfoController().update_company(designer.id, **details)


def test_rejects_registration_number_of_another_company(designer, other_designer, company):
    CreateCompanyProfileController().create_company(other_designer.id, "Olly Co", "OLLY-0001", "3 Side St", "",
                                                    "olly@co.sg", "")
    with pytest.raises(ValueError, match="already registered"):
        UpdateCompanyInfoController().update_company(designer.id, "Dana", "OLLY-0001", "1 Main St", "",
                                                     "hello@dana.sg", "")


def test_designer_without_company_must_create_one_first(designer):
    with pytest.raises(LookupError):
        UpdateCompanyInfoController().update_company(designer.id, "X", "ABCDE1", "Addr", "", "x@y.sg", "")
