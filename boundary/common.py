"""Helpers shared by every boundary: role checks, reading the logged-in user and JSON replies."""
from functools import wraps

from flask import flash, jsonify, redirect, request, session, url_for

from control.logout_controller import LogoutController
from control.search_user_account_controller import SearchUserAccountController
from control.search_user_profile_controller import SearchUserProfileController

HOME_PAGES = {
    "UserAdmin": "account.list_accounts",
    "InteriorDesigner": "portfolio.my_idps",
    "Customer": "idp.search",
    "PlatformManager": "platform.dashboard",
}


def role_required(*roles):
    """Only lets users with one of these roles open the page; everyone else goes to the login page."""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if session.get("role") not in roles:
                flash("Please log in with an account that can open that page.", "warning")
                return redirect(url_for("auth.login"))
            return view(*args, **kwargs)
        return wrapped
    return decorator


def api_error(code, message, status):
    """The one JSON error shape the React app understands: {"error": {"code", "message"}}."""
    return jsonify(error={"code": code, "message": message}), status


def api_role_required(role):
    """role_required for the JSON API used by React.

    Checks the account and its profile in the database on every request instead of
    trusting the role saved in the session cookie, so a suspended account or profile
    is logged out straight away (401). A different role gets 403.
    """
    article = "An" if role[0] in "AEIOU" else "A"

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            account_id = current_user_id()
            account = SearchUserAccountController().view(account_id) if isinstance(account_id, int) else None
            profiles = SearchUserProfileController().search() if account else []
            profile = next((p for p in profiles if p.name == account.role), None) if account else None
            if account is None or account.is_suspended() or profile is None or profile.status != "Active":
                LogoutController().logout(session)
                return api_error("authentication_required", "Please log in with an active account.", 401)
            if account.role != role:
                return api_error("forbidden", f"{article} {role} account is required.", 403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def json_body():
    """The request's JSON object. Raises ValueError (shown as 400) for anything else."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")
    return payload


def as_text(value):
    """Form-style text for a controller: lists become "a, b", numbers become strings, None stays None."""
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, bool):
        raise ValueError("Expected text, not true/false.")
    if isinstance(value, (int, float)):
        return str(value)
    return value


def current_user_id():
    return session.get("user_id")


def home_page(role):
    return url_for(HOME_PAGES.get(role, "idp.search"))


def uploaded_file(field):
    """Returns (filename, bytes) from an <input type=file>, or (None, b'') if nothing was chosen."""
    file = request.files.get(field)
    if file is None or not file.filename:
        return None, b""
    return file.filename, file.read()
