"""Control: SuspendUserAccountController (US-42 Suspend and reactivate user account)."""
from entity.user_account import UserAccount


class SuspendUserAccountController:
    def suspend(self, admin_id, account_id):
        """Returns 'suspended', 'already_suspended', 'self' or 'not_found'.
        Suspending keeps all data; the user simply can no longer log in."""
        account = UserAccount.find_by_id(account_id)
        if account is None:
            return "not_found"
        if account.id == admin_id:
            return "self"
        if account.is_suspended():
            return "already_suspended"
        account.suspend()
        return "suspended"

    def reactivate(self, account_id):
        """Returns 'reactivated', 'already_active' or 'not_found'."""
        account = UserAccount.find_by_id(account_id)
        if account is None:
            return "not_found"
        if not account.is_suspended():
            return "already_active"
        account.reactivate()
        return "reactivated"
