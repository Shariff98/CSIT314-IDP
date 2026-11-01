"""US-42 Suspend and reactivate user account."""
from control.login_controller import LoginController
from control.suspend_user_account_controller import SuspendUserAccountController
from entity.user_account import UserAccount


def test_suspended_user_cannot_log_in_but_data_is_kept(admin, customer):
    assert SuspendUserAccountController().suspend(admin.id, customer.id) == "suspended"
    assert LoginController().login("chris@example.com", "pass123") is None
    assert UserAccount.find_by_id(customer.id).status == "Suspended"      # not deleted


def test_reactivated_user_can_log_in_again(admin, customer):
    controller = SuspendUserAccountController()
    controller.suspend(admin.id, customer.id)
    assert controller.reactivate(customer.id) == "reactivated"
    assert LoginController().login("chris@example.com", "pass123").id == customer.id


def test_suspending_twice_is_reported(admin, customer):
    controller = SuspendUserAccountController()
    controller.suspend(admin.id, customer.id)
    assert controller.suspend(admin.id, customer.id) == "already_suspended"


def test_reactivating_an_active_account_is_reported(customer):
    assert SuspendUserAccountController().reactivate(customer.id) == "already_active"


def test_admin_cannot_suspend_themselves(admin):
    assert SuspendUserAccountController().suspend(admin.id, admin.id) == "self"
    assert not UserAccount.find_by_id(admin.id).is_suspended()


def test_unknown_account(admin):
    controller = SuspendUserAccountController()
    assert controller.suspend(admin.id, 999) == "not_found"
    assert controller.reactivate(999) == "not_found"
