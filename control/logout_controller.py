"""Control: LogoutController (US-01 Log out)."""


class LogoutController:
    def logout(self, session):
        """Removes everything about the user from their session. Returns True if someone was logged in."""
        was_logged_in = "user_id" in session
        session.clear()
        return was_logged_in
