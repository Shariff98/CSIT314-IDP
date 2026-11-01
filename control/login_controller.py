"""Control: LoginController (US-23 Log in)."""
from entity.user_account import UserAccount
from entity.user_profile import UserProfile


class LoginController:
    def login(self, email, password):
        """Returns the UserAccount on success, or None.
        Fails for a wrong password, a suspended account, or a suspended user profile."""
        account = UserAccount.find_by_email((email or "").strip())
        if account is None or account.is_suspended():
            return None
        if not account.check_password(password):
            return None
        profile = UserProfile.find_by_name(account.role)
        if profile is not None and profile.is_suspended():
            return None
        return account
