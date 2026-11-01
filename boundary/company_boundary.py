"""Boundary for company information: designer pages (US-24, 02, 32, 25, 12, 14, 13, 52, 15)
and the public company page customers see (US-53)."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from boundary.common import current_user_id, role_required, uploaded_file
from control.create_company_profile_controller import CreateCompanyProfileController
from control.manage_team_member_controller import ManageTeamMemberController
from control.update_company_info_controller import UpdateCompanyInfoController
from control.update_credentials_controller import UpdateCredentialsController
from control.update_services_controller import UpdateServicesController
from control.update_specialisations_controller import UpdateSpecialisationsController
from control.upload_company_image_controller import UploadCompanyImageController
from control.view_company_info_controller import ViewCompanyInfoController
from control.view_company_page_controller import ViewCompanyPageController

bp = Blueprint("company", __name__)
designer_only = role_required("InteriorDesigner")
INFO_FIELDS = ("name", "registration_no", "address", "phone", "email", "description")


@bp.route("/company")
@designer_only
def view_info():
    company = ViewCompanyInfoController().view(current_user_id())
    if company is None:
        flash("You haven't created your company profile yet.", "info")
        return redirect(url_for("company.create"))
    return render_template("company/info.html", company=company)


@bp.route("/company/new", methods=["GET", "POST"])
@designer_only
def create():
    if request.method == "POST":
        f = request.form
        try:
            CreateCompanyProfileController().create_company(current_user_id(), *(f.get(k) for k in INFO_FIELDS))
        except ValueError as error:
            flash(str(error), "danger")
            return render_template("company/form.html", form=f, creating=True), 400
        flash("Company profile created.", "success")
        return redirect(url_for("company.view_info"))
    return render_template("company/form.html", form={}, creating=True)


def _edit_page(status=200):
    company = ViewCompanyInfoController().view(current_user_id())
    if company is None:
        return redirect(url_for("company.create"))
    return render_template("company/edit.html", company=company, form=request.form or vars(company)), status


@bp.route("/company/edit", methods=["GET", "POST"])
@designer_only
def edit():
    if request.method == "POST":
        f = request.form
        try:
            UpdateCompanyInfoController().update_company(current_user_id(), *(f.get(k) for k in INFO_FIELDS))
        except LookupError:
            return redirect(url_for("company.create"))
        except ValueError as error:
            flash(str(error), "danger")
            return _edit_page(400)
        flash("Company information updated.", "success")
        return redirect(url_for("company.view_info"))
    return _edit_page()


def _section_update(action, message):
    try:
        action()
    except LookupError:
        return redirect(url_for("company.create"))
    except ValueError as error:
        flash(str(error), "danger")
        return redirect(url_for("company.edit"))
    flash(message, "success")
    return redirect(url_for("company.edit"))


@bp.route("/company/specialisations", methods=["POST"])
@designer_only
def specialisations():
    f = request.form
    return _section_update(lambda: UpdateSpecialisationsController().update(
        current_user_id(), f.get("specialisations"), f.get("service_areas")), "Specialisations updated.")


@bp.route("/company/credentials", methods=["POST"])
@designer_only
def credentials():
    f = request.form
    return _section_update(lambda: UpdateCredentialsController().update(
        current_user_id(), f.get("certifications"), f.get("awards"), f.get("years_experience")),
        "Credentials updated.")


@bp.route("/company/services", methods=["POST"])
@designer_only
def services():
    f = request.form
    return _section_update(lambda: UpdateServicesController().update(
        current_user_id(), f.get("budget_min"), f.get("budget_max"), f.get("services")), "Services updated.")


@bp.route("/company/team", methods=["POST"])
@designer_only
def add_team_member():
    f = request.form
    return _section_update(lambda: ManageTeamMemberController().add(current_user_id(), f.get("name"),
                                                                    f.get("position")), "Team member added.")


@bp.route("/company/team/<int:member_id>/delete", methods=["POST"])
@designer_only
def remove_team_member(member_id):
    return _section_update(lambda: ManageTeamMemberController().remove(current_user_id(), member_id),
                           "Team member removed.")


@bp.route("/company/images", methods=["POST"])
@designer_only
def upload_image():
    filename, data = uploaded_file("image")
    return _section_update(lambda: UploadCompanyImageController().upload(
        current_user_id(), request.form.get("kind"), filename or "", data), "Image uploaded.")


@bp.route("/company/preview")
@designer_only
def preview():
    page = ViewCompanyPageController().view(current_user_id())
    if page is None:
        return redirect(url_for("company.create"))
    return render_template("company/page.html", preview=True, **page)


@bp.route("/designers/<int:designer_id>")
def public_page(designer_id):
    page = ViewCompanyPageController().view(designer_id)
    if page is None:
        abort(404)
    return render_template("company/page.html", preview=False, **page)
