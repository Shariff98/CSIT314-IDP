"""Feature 1: user accounts and profiles.
US-01 Log out, US-11 Update and suspend profile, US-22 Search accounts, US-23 Log in,
US-31 Search profiles, US-41 Update account, US-43 Self-registration, US-51 Create profile."""
import pytest

from control.create_user_profile_controller import CreateUserProfileController
from control.login_controller import LoginController
from control.logout_controller import LogoutController
from control.register_customer_controller import RegisterCustomerController
from control.search_user_account_controller import SearchUserAccountController
from control.search_user_profile_controller import SearchUserProfileController
from control.update_user_account_controller import UpdateUserAccountController
from control.update_user_profile_controller import UpdateUserProfileController
from entity.user_account import UserAccount
from entity.user_profile import UserProfile


# ---------- US-23 Log in ----------
def test_login_with_correct_details_returns_account(customer):
    assert LoginController().login("chris@example.com", "pass123").id == customer.id


def test_login_ignores_email_case(customer):
    assert LoginController().login("Chris@Example.COM", "pass123").id == customer.id


def test_login_with_wrong_password_fails(customer):
    assert LoginController().login("chris@example.com", "wrong") is None


def test_login_with_unknown_email_fails(app):
    assert LoginController().login("nobody@example.com", "pass123") is None


def test_suspended_account_cannot_log_in(customer):
    customer.suspend()
    assert LoginController().login("chris@example.com", "pass123") is None


def test_account_in_suspended_profile_cannot_log_in(customer):
    UserProfile.find_by_name("Customer").suspend()
    assert LoginController().login("chris@example.com", "pass123") is None


# ---------- US-01 Log out ----------
def test_logout_clears_the_session():
    session = {"user_id": 1, "role": "Customer"}
    assert LogoutController().logout(session) is True
    assert session == {}


def test_logout_when_not_logged_in():
    assert LogoutController().logout({}) is False


# ---------- US-43 Customer self-registration ----------
def test_register_creates_customer_account(app):
    account = RegisterCustomerController().register("New Person", "new@example.com", "longpassword", "longpassword")
    assert account.role == "Customer"
    assert LoginController().login("new@example.com", "longpassword") is not None


@pytest.mark.parametrize("password, confirm, message", [("short", "short", "8 characters"),
                                                        ("longpassword", "different1", "do not match")])
def test_register_rejects_bad_passwords(app, password, confirm, message):
    with pytest.raises(ValueError, match=message):
        RegisterCustomerController().register("N", "n@example.com", password, confirm)


def test_register_rejects_taken_email(customer):
    with pytest.raises(ValueError, match="already exists"):
        RegisterCustomerController().register("N", "chris@example.com", "longpassword", "longpassword")


# ---------- US-22 View and search user accounts ----------
def test_search_accounts_by_keyword_role_and_status(admin, customer, designer):
    controller = SearchUserAccountController()
    assert [a.email for a in controller.search("chris")] == ["chris@example.com"]
    assert [a.email for a in controller.search("@example.com", role="InteriorDesigner")] == ["dana@example.com"]
    customer.suspend()
    assert [a.id for a in controller.search(status="Suspended")] == [customer.id]
    assert len(controller.search()) == 3


def test_search_accounts_ignores_unknown_status(customer):
    assert len(SearchUserAccountController().search(status="Deleted")) == 1


# ---------- US-41 Update user account ----------
def test_update_account_changes_details(customer):
    UpdateUserAccountController().update_account(customer.id, "Chris C", "chris.c@example.com", "InteriorDesigner")
    saved = UserAccount.find_by_id(customer.id)
    assert (saved.name, saved.email, saved.role) == ("Chris C", "chris.c@example.com", "InteriorDesigner")


def test_update_account_rejects_email_of_another_account(customer, designer):
    with pytest.raises(ValueError, match="Another account"):
        UpdateUserAccountController().update_account(customer.id, "Chris", "dana@example.com", "Customer")


def test_update_account_keeps_own_email(customer):
    UpdateUserAccountController().update_account(customer.id, "Renamed", "chris@example.com", "Customer")
    assert UserAccount.find_by_id(customer.id).name == "Renamed"


def test_update_unknown_account(app):
    with pytest.raises(LookupError):
        UpdateUserAccountController().update_account(999, "X", "x@example.com", "Customer")


# ---------- US-51 Create user profile ----------
def test_create_profile(app):
    profile = CreateUserProfileController().create_profile("Moderator", "Reviews reported projects")
    assert profile.status == "Active"
    assert UserProfile.find_by_name("moderator").id == profile.id


@pytest.mark.parametrize("name, message", [("Customer", "already exists"), ("Bad<Name>", "letters"),
                                           ("", "name")])
def test_create_profile_rejects_bad_names(app, name, message):
    with pytest.raises(ValueError, match=message):
        CreateUserProfileController().create_profile(name, "Something")


# ---------- US-31 View and search user profiles ----------
def test_search_profiles(app):
    controller = SearchUserProfileController()
    assert [p.name for p in controller.search()] == ["Customer", "InteriorDesigner", "PlatformManager", "UserAdmin"]
    assert [p.name for p in controller.search("categories")] == ["PlatformManager"]


def test_profile_shows_how_many_accounts_use_it(customer):
    assert UserProfile.find_by_name("Customer").account_count() == 1


# ---------- US-11 Update and suspend user profile ----------
def test_rename_custom_profile_moves_its_accounts(app):
    profile = CreateUserProfileController().create_profile("Moderator", "Reviews")
    UserAccount.create("Mod", "mod@example.com", "pass123", "Moderator")
    UpdateUserProfileController().update_profile(profile.id, "Reviewer", "Reviews projects")
    assert UserAccount.find_by_email("mod@example.com").role == "Reviewer"


def test_built_in_profile_cannot_be_renamed_but_description_can_change(app):
    profile = UserProfile.find_by_name("Customer")
    controller = UpdateUserProfileController()
    with pytest.raises(ValueError, match="cannot be renamed"):
        controller.update_profile(profile.id, "Client", "x")
    controller.update_profile(profile.id, "Customer", "Homeowners looking for designers")
    assert UserProfile.find_by_id(profile.id).description == "Homeowners looking for designers"


def test_suspend_and_reactivate_profile(customer):
    profile = UserProfile.find_by_name("Customer")
    controller = UpdateUserProfileController()
    assert controller.suspend(profile.id) == "suspended"
    assert controller.suspend(profile.id) == "already_suspended"
    assert controller.reactivate(profile.id) == "reactivated"
    assert LoginController().login("chris@example.com", "pass123") is not None


def test_user_admin_profile_is_protected(app):
    assert UpdateUserProfileController().suspend(UserProfile.find_by_name("UserAdmin").id) == "protected"
