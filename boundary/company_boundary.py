"""Boundary for company information: designer pages (US-24, 02, 32, 25, 12, 14, 13, 52, 15)
and the public company page customers see (US-53).

The HTML pages and the JSON API for React call the same controllers."""
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for

from boundary.common import (api_error, api_role_required, as_text, current_user_id, json_body, role_required,
                             uploaded_file)
from boundary.project_serializer import company_json, project_json, team_json
from control.browse_designers_controller import BrowseDesignersController
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
api_bp = Blueprint("company_api", __name__, url_prefix="/api/designer")
designer_only = role_required("InteriorDesigner")
api_designer_required = api_role_required("InteriorDesigner")
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


# ---------- JSON API: public designer directory and company page ----------

def _image_url(photo):
    return url_for("idp.uploaded", filename=photo.filename) if photo else None


@bp.route("/api/designers")
def api_designers():
    """Customers browse active design companies, then open one company page (US-53)."""
    a = request.args
    controller = BrowseDesignersController()
    try:
        rows = controller.browse(a.get("q", ""), a.get("specialisation"), a.get("service_area"), a.get("max_budget"))
    except ValueError as error:
        return api_error("invalid_request", str(error), 400)
    items = [{**company_json(row["company"]), "project_count": row["projects"],
              "preview_url": _image_url(row["preview"])} for row in rows]
    return jsonify(data={"items": items, "total": len(items), "options": controller.options()})


@bp.route("/api/designers/<int:designer_id>")
def api_company_page(designer_id):
    """US-53 View interior designer company page (also the designer's own preview, US-15)."""
    page = ViewCompanyPageController().view(designer_id)
    if page is None:
        return api_error("not_found", "This designer's page is not available.", 404)
    return jsonify(data={"designer": {"id": page["designer"].id, "name": page["designer"].name},
                         "company": company_json(page["company"]),
                         "team": [team_json(member) for member in page["team"]],
                         "projects": [project_json(project) for project in page["projects"]]})


# ---------- JSON API: the designer's own company profile ----------

def _my_company(status=200):
    company = ViewCompanyInfoController().view(current_user_id())
    return jsonify(data={"company": company_json(company),
                         "team": [team_json(member) for member in company.team_members()] if company else []}), status


def _company_call(action, status=200):
    """Runs one company controller call, then returns the updated company (or a JSON error)."""
    try:
        action()
    except LookupError:
        return api_error("no_company", "Create your company profile first.", 404)
    except ValueError as error:
        return api_error("invalid_request", str(error), 400)
    return _my_company(status)


def _info_fields():
    p = json_body()
    values = [p.get(field) for field in INFO_FIELDS]
    if any(value is not None and not isinstance(value, str) for value in values):
        raise ValueError("Company details must be text")
    return values


@api_bp.route("/company", methods=["GET"])
@api_designer_required
def api_view_company():
    """US-02 View company information. "company" is null until the profile is created."""
    return _my_company()


@api_bp.route("/company", methods=["POST"])
@api_designer_required
def api_create_company():
    """US-24 Create company profile."""
    return _company_call(lambda: CreateCompanyProfileController().create_company(current_user_id(), *_info_fields()),
                         201)


@api_bp.route("/company", methods=["PUT"])
@api_designer_required
def api_update_company():
    """US-32 Update company information."""
    return _company_call(lambda: UpdateCompanyInfoController().update_company(current_user_id(), *_info_fields()))


@api_bp.route("/company/specialisations", methods=["PUT"])
@api_designer_required
def api_update_specialisations():
    """US-25 Specialisations and service areas (text "a, b" or a list)."""
    def update():
        p = json_body()
        UpdateSpecialisationsController().update(current_user_id(), as_text(p.get("specialisations")),
                                                 as_text(p.get("service_areas")))
    return _company_call(update)


@api_bp.route("/company/credentials", methods=["PUT"])
@api_designer_required
def api_update_credentials():
    """US-12 Certifications, awards and years of experience."""
    def update():
        p = json_body()
        UpdateCredentialsController().update(current_user_id(), as_text(p.get("certifications")),
                                             as_text(p.get("awards")), as_text(p.get("years_experience")))
    return _company_call(update)


@api_bp.route("/company/services", methods=["PUT"])
@api_designer_required
def api_update_services():
    """US-14 Budget range and services offered."""
    def update():
        p = json_body()
        UpdateServicesController().update(current_user_id(), as_text(p.get("budget_min")),
                                          as_text(p.get("budget_max")), as_text(p.get("services")))
    return _company_call(update)


@api_bp.route("/company/team", methods=["POST"])
@api_designer_required
def api_add_team_member():
    """US-13 Add a team member."""
    def add():
        p = json_body()
        ManageTeamMemberController().add(current_user_id(), as_text(p.get("name")), as_text(p.get("position")))
    return _company_call(add, 201)


@api_bp.route("/company/team/<int:member_id>", methods=["DELETE"])
@api_designer_required
def api_remove_team_member(member_id):
    """US-13 Remove a team member (only from the designer's own company)."""
    def remove():
        if not ManageTeamMemberController().remove(current_user_id(), member_id):
            raise ValueError("Team member not found")
    return _company_call(remove)


@api_bp.route("/company/images", methods=["POST"])
@api_designer_required
def api_upload_company_image():
    """US-52 Upload the logo or cover image (multipart: kind=logo|cover, image=<file>)."""
    def upload():
        filename, data = uploaded_file("image")
        if not filename:
            raise ValueError("Choose an image to upload")
        UploadCompanyImageController().upload(current_user_id(), request.form.get("kind"), filename, data)
    return _company_call(upload)
