"""Control: RegisterCustomerController (US-43 Customer self-registration)."""
from control.create_user_account_controller import MIN_PASSWORD
from control.validation import check_email, clean, require
from entity.user_account import UserAccount


class RegisterCustomerController:
    def register(self, name, email, password, confirm_password):
        """A visitor creates their own Customer account (never any other role)."""
        require(name=name, email=email, password=password)
        email = check_email(email)
        if len(password) < MIN_PASSWORD:
            raise ValueError(f"Password must be at least {MIN_PASSWORD} characters")
        if password != confirm_password:
            raise ValueError("Passwords do not match")
        if UserAccount.find_by_email(email) is not None:
            raise ValueError("An account with this email already exists")
        return UserAccount.create(clean(name), email, password, "Customer")
