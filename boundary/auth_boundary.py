"""Boundary: LoginPage (US-23), Log out link (US-01), RegisterPage (US-43)."""
from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for

from boundary.common import home_page
from control.login_controller import LoginController
from control.logout_controller import LogoutController
from control.register_customer_controller import RegisterCustomerController
from control.search_user_account_controller import SearchUserAccountController
from control.search_user_profile_controller import SearchUserProfileController

bp = Blueprint("auth", __name__)


def _api_error(code, message, status):
    return jsonify(error={"code": code, "message": message}), status


def _json_fields(*names):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")
    if any(not isinstance(payload.get(name), str) or not payload[name].strip() for name in names):
        raise ValueError("Required fields must be non-empty strings: " + ", ".join(names))
    return [payload[name] for name in names]


def _user_data(account):
    # Explicit allowlist: never serialize the account's password hash.
    return {key: getattr(account, key) for key in ("id", "name", "email", "role", "status")}


def _start_session(account):
    session.clear()
    session.update(user_id=account.id, role=account.role, name=account.name)


@bp.route("/api/auth/login", methods=["POST"])
def api_login():
    try:
        email, password = _json_fields("email", "password")
    except ValueError as error:
        return _api_error("invalid_request", str(error), 400)
    account = LoginController().login(email, password)
    if account is None:
        return _api_error("invalid_credentials", "Invalid email or password, or the account is suspended.", 401)
    _start_session(account)
    return jsonify(data={"user": _user_data(account)})


@bp.route("/api/customers/register", methods=["POST"])
def api_register():
    try:
        fields = _json_fields("name", "email", "password", "confirm_password")
        account = RegisterCustomerController().register(*fields)
    except ValueError as error:
        return _api_error("invalid_request", str(error), 400)
    return jsonify(data={"user": _user_data(account), "login_required": True}), 201


@bp.route("/api/auth/me", methods=["GET"])
def api_me():
    account_id = session.get("user_id")
    account = SearchUserAccountController().view(account_id) if account_id is not None else None
    profiles = SearchUserProfileController().search(status="Suspended") if account else []
    if account is None or account.is_suspended() or any(p.name == account.role for p in profiles):
        LogoutController().logout(session)
        return _api_error("authentication_required", "Please log in.", 401)
    # Refresh session values if an administrator changed the account.
    session.update(role=account.role, name=account.name)
    return jsonify(data={"user": _user_data(account)})


@bp.route("/api/auth/logout", methods=["POST"])
def api_logout():
    LogoutController().logout(session)
    return jsonify(data={"logged_out": True})


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        account = LoginController().login(request.form.get("email"), request.form.get("password"))
        if account is None:
            flash("Invalid email or password, or the account is suspended.", "danger")
            return render_template("login.html"), 401
        _start_session(account)
        return redirect(home_page(account.role))
    return render_template("login.html")


@bp.route("/logout")
def logout():
    if LogoutController().logout(session):
        flash("You have been logged out.", "success")
    if current_app.config.get("REACT_APP"):
        return redirect("/#/login")   # production: one front door, the React app
    return redirect(url_for("auth.login"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        f = request.form
        try:
            RegisterCustomerController().register(f.get("name"), f.get("email"), f.get("password"),
                                                  f.get("confirm_password"))
        except ValueError as error:
            flash(str(error), "danger")
            return render_template("register.html", form=f), 400
        flash("Account created. You can log in now.", "success")
        return redirect(url_for("auth.login"))
    return render_template("register.html", form={})
