"""Control: UpdateUserProfileController (US-11 Update and suspend user profile)."""
from control.validation import clean, require
from entity.db import BUILT_IN_PROFILES
from entity.user_profile import UserProfile

BUILT_IN = {name for name, _ in BUILT_IN_PROFILES}


class UpdateUserProfileController:
    def update_profile(self, profile_id, name, description):
        profile = UserProfile.find_by_id(profile_id)
        if profile is None:
            raise LookupError("Profile not found")
        require(name=name, description=description)
        name = clean(name)
        if profile.name in BUILT_IN and name != profile.name:
            raise ValueError("Built-in profiles cannot be renamed, because permissions depend on them")
        other = UserProfile.find_by_name(name)
        if other is not None and other.id != profile.id:
            raise ValueError("A profile with this name already exists")
        profile.update(name, clean(description))
        return profile

    def suspend(self, profile_id):
        """Accounts in a suspended profile cannot log in. Returns a result string."""
        profile = UserProfile.find_by_id(profile_id)
        if profile is None:
            return "not_found"
        if profile.name == "UserAdmin":
            return "protected"            # suspending it would lock every admin out
        if profile.is_suspended():
            return "already_suspended"
        profile.suspend()
        return "suspended"

    def reactivate(self, profile_id):
        profile = UserProfile.find_by_id(profile_id)
        if profile is None:
            return "not_found"
        if not profile.is_suspended():
            return "already_active"
        profile.reactivate()
        return "reactivated"
