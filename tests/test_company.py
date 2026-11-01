"""Feature 2: designer company information.
US-02 View, US-12 Credentials, US-13 Team members, US-14 Budget and services, US-15 Preview,
US-24 Create, US-25 Specialisations, US-52 Logo and cover, US-53 Customer views company page."""
import os

import pytest

from control.create_company_profile_controller import CreateCompanyProfileController
from control.manage_team_member_controller import ManageTeamMemberController
from control.update_credentials_controller import UpdateCredentialsController
from control.update_services_controller import UpdateServicesController
from control.update_specialisations_controller import UpdateSpecialisationsController
from control.upload_company_image_controller import UploadCompanyImageController
from control.view_company_info_controller import ViewCompanyInfoController
from control.view_company_page_controller import ViewCompanyPageController
from entity import storage
from tests.conftest import PNG


@pytest.fixture
def company(designer):
    return CreateCompanyProfileController().create_company(
        designer.id, "Dana Interiors", "201912345K", "1 Main St", "6123 4567", "hello@dana.sg", "We design homes")


# ---------- US-24 Create company profile / US-02 View company information ----------
def test_create_and_view_company(designer, company):
    saved = ViewCompanyInfoController().view(designer.id)
    assert (saved.name, saved.registration_no, saved.email) == ("Dana Interiors", "201912345K", "hello@dana.sg")


def test_view_returns_none_before_company_exists(designer):
    assert ViewCompanyInfoController().view(designer.id) is None


def test_designer_can_only_have_one_company(designer, company):
    with pytest.raises(ValueError, match="already have"):
        CreateCompanyProfileController().create_company(designer.id, "Second", "OTHER-1", "a", "", "a@b.co", "")


def test_create_company_requires_address(designer):
    with pytest.raises(ValueError, match="address"):
        CreateCompanyProfileController().create_company(designer.id, "X", "ABCDE1", " ", "", "a@b.co", "")


# ---------- US-25 Specialisations and service areas ----------
def test_specialisations_are_cleaned_and_listed(designer, company):
    UpdateSpecialisationsController().update(designer.id, " modern, Minimalist,,modern ", "Central, East")
    saved = ViewCompanyInfoController().view(designer.id)
    assert saved.specialisation_list == ["Modern", "Minimalist"]
    assert saved.service_area_list == ["Central", "East"]


def test_specialisations_required(designer, company):
    with pytest.raises(ValueError, match="specialisation"):
        UpdateSpecialisationsController().update(designer.id, " , ", "Central")


# ---------- US-12 Certifications, awards and experience ----------
def test_update_credentials(designer, company):
    UpdateCredentialsController().update(designer.id, "BCA Green Mark", "Best Kitchen 2025", "12")
    saved = ViewCompanyInfoController().view(designer.id)
    assert (saved.certifications, saved.awards, saved.years_experience) == ("BCA Green Mark", "Best Kitchen 2025", 12)


@pytest.mark.parametrize("years", ["-1", "200", "lots"])
def test_rejects_bad_years_of_experience(designer, company, years):
    with pytest.raises(ValueError, match="Years of experience"):
        UpdateCredentialsController().update(designer.id, "", "", years)


# ---------- US-14 Budget range and services ----------
def test_update_budget_and_services(designer, company):
    UpdateServicesController().update(designer.id, "20000", "80000", "Full renovation, Carpentry")
    saved = ViewCompanyInfoController().view(designer.id)
    assert (saved.budget_min, saved.budget_max) == (20000, 80000)
    assert saved.service_list == ["Full renovation", "Carpentry"]


def test_budget_min_cannot_exceed_max(designer, company):
    with pytest.raises(ValueError, match="Minimum budget"):
        UpdateServicesController().update(designer.id, 90000, 1000, "Carpentry")


# ---------- US-13 Team members ----------
def test_add_and_remove_team_member(designer, company):
    controller = ManageTeamMemberController()
    member = controller.add(designer.id, "Jo Tan", "Lead designer")
    assert [m.name for m in company.team_members()] == ["Jo Tan"]
    assert controller.remove(designer.id, member.id) is True
    assert company.team_members() == []


def test_cannot_remove_another_companys_member(designer, other_designer, company):
    member = ManageTeamMemberController().add(designer.id, "Jo Tan", "Lead designer")
    CreateCompanyProfileController().create_company(other_designer.id, "Olly", "OLLY-1", "a", "", "o@o.co", "")
    assert ManageTeamMemberController().remove(other_designer.id, member.id) is False


# ---------- US-52 Logo and cover image ----------
def test_upload_logo_replaces_old_file(designer, company):
    controller = UploadCompanyImageController()
    first = controller.upload(designer.id, "logo", "logo.png", PNG).logo_file
    second = controller.upload(designer.id, "logo", "logo2.PNG", PNG).logo_file
    assert first != second
    assert not os.path.exists(os.path.join(storage.upload_dir(), first))
    assert os.path.exists(os.path.join(storage.upload_dir(), second))


@pytest.mark.parametrize("filename, data, message", [("cv.pdf", PNG, "Only JPG"), ("a.png", b"", "empty"),
                                                     ("a.png", b"x" * (5 * 1024 * 1024 + 1), "5 MB")])
def test_upload_rejects_bad_files(designer, company, filename, data, message):
    with pytest.raises(ValueError, match=message):
        UploadCompanyImageController().upload(designer.id, "cover", filename, data)


# ---------- US-53 Customer views company page / US-15 Preview ----------
def test_company_page_shows_only_published_projects(designer, company, make_idp):
    make_idp("Public")
    make_idp("Draft", published=False)
    page = ViewCompanyPageController().view(designer.id)
    assert page["company"].name == "Dana Interiors"
    assert [p.title for p in page["projects"]] == ["Public"]


def test_company_page_hidden_for_suspended_designer(designer, company):
    designer.suspend()
    assert ViewCompanyPageController().view(designer.id) is None


def test_company_page_missing_when_no_company(designer, customer):
    assert ViewCompanyPageController().view(designer.id) is None
    assert ViewCompanyPageController().view(customer.id) is None
