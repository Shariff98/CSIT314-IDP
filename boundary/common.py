"""Helpers shared by every boundary: role checks and reading the logged-in user."""
from functools import wraps

from flask import flash, redirect, session, url_for

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


def current_user_id():
    return session.get("user_id")


def home_page(role):
    return url_for(HOME_PAGES.get(role, "idp.search"))


def uploaded_file(field):
    """Returns (filename, bytes) from an <input type=file>, or (None, b'') if nothing was chosen."""
    from flask import request
    file = request.files.get(field)
    if file is None or not file.filename:
        return None, b""
    return file.filename, file.read()
