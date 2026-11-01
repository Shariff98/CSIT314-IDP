"""Boundary: LoginPage (US-23), Log out link (US-01), RegisterPage (US-43)."""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from boundary.common import home_page
from control.login_controller import LoginController
from control.logout_controller import LogoutController
from control.register_customer_controller import RegisterCustomerController

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        account = LoginController().login(request.form.get("email"), request.form.get("password"))
        if account is None:
            flash("Invalid email or password, or the account is suspended.", "danger")
            return render_template("login.html"), 401
        session.clear()
        session["user_id"] = account.id
        session["role"] = account.role
        session["name"] = account.name
        return redirect(home_page(account.role))
    return render_template("login.html")


@bp.route("/logout")
def logout():
    if LogoutController().logout(session):
        flash("You have been logged out.", "success")
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
