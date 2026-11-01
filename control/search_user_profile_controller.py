"""Control: SearchUserProfileController (US-31 View and search user profiles)."""
from entity.user_profile import UserProfile


class SearchUserProfileController:
    def search(self, keyword="", status=None):
        status = status if status in ("Active", "Suspended") else None
        return UserProfile.search((keyword or "").strip(), status)

    def view(self, profile_id):
        return UserProfile.find_by_id(profile_id)
