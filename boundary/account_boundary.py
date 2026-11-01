"""Boundary for User Admin: user account pages (US-21, 22, 41, 42) and user profile pages (US-51, 31, 11)."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from boundary.common import current_user_id, role_required
from control.create_user_account_controller import CreateUserAccountController
from control.create_user_profile_controller import CreateUserProfileController
from control.search_user_account_controller import SearchUserAccountController
from control.search_user_profile_controller import SearchUserProfileController
from control.suspend_user_account_controller import SuspendUserAccountController
from control.update_user_account_controller import UpdateUserAccountController
from control.update_user_profile_controller import UpdateUserProfileController

bp = Blueprint("account", __name__, url_prefix="/admin")
admin_only = role_required("UserAdmin")

RESULT_MESSAGES = {
    "suspended": ("Account suspended.", "success"),
    "already_suspended": ("That account is already suspended.", "info"),
    "self": ("You cannot suspend your own account.", "danger"),
    "reactivated": ("Account reactivated.", "success"),
    "already_active": ("That account is already active.", "info"),
    "protected": ("The UserAdmin profile cannot be suspended.", "danger"),
}


def profile_names():
    return [p.name for p in SearchUserProfileController().search(status="Active")]


# ---------- user accounts ----------
@bp.route("/accounts")
@admin_only
def list_accounts():
    a = request.args
    accounts = SearchUserAccountController().search(a.get("q", ""), a.get("role"), a.get("status"))
    return render_template("admin/accounts.html", accounts=accounts, roles=profile_names(), args=a)


@bp.route("/accounts/new", methods=["GET", "POST"])
@admin_only
def create_account():
    if request.method == "POST":
        f = request.form
        try:
            account = CreateUserAccountController().create_account(f.get("name"), f.get("email"),
                                                                    f.get("password"), f.get("role"))
        except ValueError as error:
            flash(str(error), "danger")
            return render_template("admin/account_form.html", form=f, roles=profile_names(), account=None), 400
        flash(f"Account created for {account.name}.", "success")
        return redirect(url_for("account.list_accounts"))
    return render_template("admin/account_form.html", form={}, roles=profile_names(), account=None)


@bp.route("/accounts/<int:account_id>/edit", methods=["GET", "POST"])
@admin_only
def edit_account(account_id):
    account = SearchUserAccountController().view(account_id)
    if account is None:
        abort(404)
    roles = [p.name for p in SearchUserProfileController().search()]
    if request.method == "POST":
        f = request.form
        try:
            UpdateUserAccountController().update_account(account_id, f.get("name"), f.get("email"), f.get("role"))
        except ValueError as error:
            flash(str(error), "danger")
            return render_template("admin/account_form.html", form=f, roles=roles, account=account), 400
        flash("Account updated.", "success")
        return redirect(url_for("account.list_accounts"))
    form = {"name": account.name, "email": account.email, "role": account.role}
    return render_template("admin/account_form.html", form=form, roles=roles, account=account)


@bp.route("/accounts/<int:account_id>/<action>", methods=["POST"])
@admin_only
def change_account_status(account_id, action):
    controller = SuspendUserAccountController()
    if action == "suspend":
        result = controller.suspend(current_user_id(), account_id)
    elif action == "reactivate":
        result = controller.reactivate(account_id)
    else:
        abort(404)
    if result == "not_found":
        abort(404)
    flash(*RESULT_MESSAGES[result])
    return redirect(request.referrer or url_for("account.list_accounts"))


# ---------- user profiles ----------
@bp.route("/profiles")
@admin_only
def list_profiles():
    a = request.args
    profiles = SearchUserProfileController().search(a.get("q", ""), a.get("status"))
    return render_template("admin/profiles.html", profiles=profiles, args=a)


@bp.route("/profiles/new", methods=["GET", "POST"])
@admin_only
def create_profile():
    if request.method == "POST":
        f = request.form
        try:
            CreateUserProfileController().create_profile(f.get("name"), f.get("description"))
        except ValueError as error:
            flash(str(error), "danger")
            return render_template("admin/profile_form.html", form=f, profile=None), 400
        flash("Profile created.", "success")
        return redirect(url_for("account.list_profiles"))
    return render_template("admin/profile_form.html", form={}, profile=None)


@bp.route("/profiles/<int:profile_id>/edit", methods=["GET", "POST"])
@admin_only
def edit_profile(profile_id):
    profile = SearchUserProfileController().view(profile_id)
    if profile is None:
        abort(404)
    if request.method == "POST":
        f = request.form
        try:
            UpdateUserProfileController().update_profile(profile_id, f.get("name"), f.get("description"))
        except ValueError as error:
            flash(str(error), "danger")
            return render_template("admin/profile_form.html", form=f, profile=profile), 400
        flash("Profile updated.", "success")
        return redirect(url_for("account.list_profiles"))
    return render_template("admin/profile_form.html", form=vars(profile), profile=profile)


@bp.route("/profiles/<int:profile_id>/<action>", methods=["POST"])
@admin_only
def change_profile_status(profile_id, action):
    controller = UpdateUserProfileController()
    if action not in ("suspend", "reactivate"):
        abort(404)
    result = getattr(controller, action)(profile_id)
    if result == "not_found":
        abort(404)
    message = {"suspended": "Profile suspended. Its accounts can no longer log in.",
               "reactivated": "Profile reactivated."}.get(result)
    flash(*((message, "success") if message else RESULT_MESSAGES[result]))
    return redirect(url_for("account.list_profiles"))
