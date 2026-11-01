"""Control: SearchUserAccountController (US-22 View and search user accounts)."""
from entity.user_account import UserAccount


class SearchUserAccountController:
    STATUSES = ("Active", "Suspended")

    def search(self, keyword="", role=None, status=None):
        """Keyword matches name or email; role and status narrow the list. Blank means 'any'."""
        status = status if status in self.STATUSES else None
        return UserAccount.search((keyword or "").strip(), role or None, status)

    def view(self, account_id):
        return UserAccount.find_by_id(account_id)
