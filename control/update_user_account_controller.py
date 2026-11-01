"""Control: UpdateUserAccountController (US-41 Update user account)."""
from control.validation import check_email, clean, require
from entity.user_account import UserAccount
from entity.user_profile import UserProfile


class UpdateUserAccountController:
    def update_account(self, account_id, name, email, role):
        account = UserAccount.find_by_id(account_id)
        if account is None:
            raise LookupError("Account not found")
        require(name=name, email=email, role=role)
        email = check_email(email)
        other = UserAccount.find_by_email(email)
        if other is not None and other.id != account.id:
            raise ValueError("Another account already uses this email")
        profile = UserProfile.find_by_name(role)
        if profile is None:
            raise ValueError("Choose an existing user profile")
        account.update(clean(name), email, profile.name)
        return account
