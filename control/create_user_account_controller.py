"""Control: CreateUserAccountController (US-21 Create user account)."""
from control.validation import check_email, clean, require
from entity.user_account import UserAccount
from entity.user_profile import UserProfile

MIN_PASSWORD = 8


class CreateUserAccountController:
    def create_account(self, name, email, password, role):
        """User Admin creates an account for any active user profile."""
        require(name=name, email=email, password=password, role=role)
        email = check_email(email)
        if len(password) < MIN_PASSWORD:
            raise ValueError(f"Password must be at least {MIN_PASSWORD} characters")
        profile = UserProfile.find_by_name(role)
        if profile is None or profile.is_suspended():
            raise ValueError("Choose an active user profile")
        if UserAccount.find_by_email(email) is not None:
            raise ValueError("An account with this email already exists")
        return UserAccount.create(clean(name), email, password, profile.name)
