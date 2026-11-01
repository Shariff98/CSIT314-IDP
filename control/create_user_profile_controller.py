"""Control: CreateUserProfileController (US-51 Create user profile)."""
from control.validation import clean, require
from entity.user_profile import UserProfile


class CreateUserProfileController:
    def create_profile(self, name, description):
        require(name=name, description=description)
        name = clean(name)
        if not name.replace(" ", "").isalnum():
            raise ValueError("Profile name can only use letters, numbers and spaces")
        if UserProfile.find_by_name(name) is not None:
            raise ValueError("A profile with this name already exists")
        return UserProfile.create(name, clean(description))
