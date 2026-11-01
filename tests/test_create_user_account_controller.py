"""US-21 Create user account."""
import pytest

from control.create_user_account_controller import CreateUserAccountController
from control.login_controller import LoginController
from entity.user_profile import UserProfile


@pytest.mark.parametrize("role", ["UserAdmin", "InteriorDesigner", "Customer", "PlatformManager"])
def test_admin_can_create_account_for_every_role(app, role):
    account = CreateUserAccountController().create_account("Sam Lee", "Sam@Example.com", "secret123", role)
    assert account.role == role
    assert account.email == "sam@example.com"          # stored in lower case
    assert account.status == "Active"


def test_new_account_can_log_in_and_password_is_hashed(app):
    account = CreateUserAccountController().create_account("Sam Lee", "sam@example.com", "secret123", "Customer")
    assert account.password_hash != "secret123"
    assert LoginController().login("sam@example.com", "secret123").id == account.id


def test_rejects_duplicate_email(customer):
    with pytest.raises(ValueError, match="already exists"):
        CreateUserAccountController().create_account("Copy", "CHRIS@example.com", "secret123", "Customer")


@pytest.mark.parametrize("name, email, password, role, message", [
    ("", "a@b.com", "secret123", "Customer", "name"),
    ("Sam", "not-an-email", "secret123", "Customer", "Email"),
    ("Sam", "a@b.com", "short", "Customer", "8 characters"),
    ("Sam", "a@b.com", "secret123", "Wizard", "profile"),
])
def test_rejects_invalid_input(app, name, email, password, role, message):
    with pytest.raises(ValueError, match=message):
        CreateUserAccountController().create_account(name, email, password, role)


def test_rejects_suspended_profile(app):
    UserProfile.find_by_name("Customer").suspend()
    with pytest.raises(ValueError, match="active user profile"):
        CreateUserAccountController().create_account("Sam", "a@b.com", "secret123", "Customer")
