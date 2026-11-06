"""Boundary: SearchIDPPage (US-07 browse, US-28 search, US-17 filter, US-18 sort),
IDPDetailPage (US-34, US-37, US-45) and CreateIDPPage (US-54)."""
import uuid

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request,
                   send_from_directory, session, url_for)

from boundary.common import current_user_id, role_required
from boundary.project_serializer import project_json
from control.browse_idp_controller import SORT_OPTIONS, BrowseIDPController
from control.create_idp_controller import CreateIDPController
from control.filter_idp_controller import FilterIDPController
from control.ownership import PROPERTY_TYPES, STYLES
from control.save_favourite_controller import SaveFavouriteController
from control.search_category_controller import SearchCategoryController
from control.search_idp_controller import SearchIDPController
from control.view_designer_projects_controller import ViewDesignerProjectsController
from control.view_idp_controller import ViewIDPController
from control.validation import to_int

bp = Blueprint("idp", __name__)

FILTERS = ("category", "style", "min_budget", "max_budget", "property_type", "location")


def form_options():
    return {"categories": SearchCategoryController().active_names(), "property_types": PROPERTY_TYPES,
            "styles": STYLES, "sort_options": SORT_OPTIONS}


def _browse_results(args):
    keyword, sort = args.get("q", ""), args.get("sort", "newest")
    if any(args.get(name) for name in FILTERS):
        return FilterIDPController().filter(keyword, *(args.get(name) for name in FILTERS), sort=sort)
    if keyword.strip():
        return SearchIDPController().search(keyword, sort)
    return BrowseIDPController().browse(sort)


@bp.route("/api/idps")
def api_search():
    try:
        page = to_int(request.args.get("page", "1"), "Page", minimum=1)
        per_page = to_int(request.args.get("per_page", "24"), "Page size", minimum=1, maximum=100)
        results = _browse_results(request.args)
    except ValueError as error:
        return jsonify(error={"code": "invalid_request", "message": str(error)}), 400
    start = (page - 1) * per_page
    return jsonify(data={"items": [project_json(project) for project in results[start:start + per_page]],
                         "total": len(results), "page": page, "per_page": per_page,
                         "pages": max(1, (len(results) + per_page - 1) // per_page)})


@bp.route("/api/idps/options")
def api_options():
    projects = BrowseIDPController().browse()
    options = form_options()
    options["styles"] = sorted(set(STYLES).union(tag for project in projects for tag in project.style_tag_list))
    options["locations"] = sorted({project.location for project in projects if project.location.strip()})
    return jsonify(data=options)


@bp.route("/api/idps/<int:idp_id>")
def api_detail(idp_id):
    view_key = session.setdefault("view_key", uuid.uuid4().hex)
    project = ViewIDPController().view(idp_id, current_user_id(), view_key)
    if project is None:
        return jsonify(error={"code": "not_found", "message": "Project not found."}), 404
    saved = session.get("role") == "Customer" and SaveFavouriteController().is_saved(current_user_id(), idp_id)
    return jsonify(data={"project": project_json(project),
                         "other_projects": [project_json(other) for other in
                                            ViewDesignerProjectsController().other_projects(idp_id)],
                         "is_saved": bool(saved)})


@bp.route("/")
def search():
    a = request.args
    keyword = a.get("q", "")
    try:
        results = _browse_results(a)
    except ValueError as error:
        flash(str(error), "danger")
        results = []
    page = max(int(a.get("page", 1)) if a.get("page", "1").isdigit() else 1, 1)
    per_page = 24
    shown = results[(page - 1) * per_page: page * per_page]
    return render_template("idp_search.html", results=shown, total=len(results), page=page,
                           pages=max((len(results) + per_page - 1) // per_page, 1), keyword=keyword,
                           args=a, **form_options())


@bp.route("/idp/<int:idp_id>")
def detail(idp_id):
    view_key = session.setdefault("view_key", uuid.uuid4().hex)
    idp = ViewIDPController().view(idp_id, current_user_id(), view_key)
    if idp is None:
        abort(404)
    others = ViewDesignerProjectsController().other_projects(idp_id)
    saved = session.get("role") == "Customer" and SaveFavouriteController().is_saved(current_user_id(), idp_id)
    return render_template("idp_detail.html", idp=idp, others=others, saved=saved)


@bp.route("/idp/new", methods=["GET", "POST"])
@role_required("InteriorDesigner")
def create():
    if request.method == "POST":
        f = request.form
        try:
            idp = CreateIDPController().create_idp(
                current_user_id(), f.get("title"), f.get("description"), f.get("category"), f.get("budget"),
                f.get("property_type"), f.get("location"), f.get("completion_date"), f.get("style_tags"),
                publish=f.get("action") != "draft")
        except ValueError as error:
            flash(str(error), "danger")
            return render_template("idp_form.html", form=f, idp=None, **form_options()), 400
        flash("Project saved as a draft." if not idp.is_published else "Project created.", "success")
        return redirect(url_for("portfolio.my_idp", idp_id=idp.id))
    return render_template("idp_form.html", form={}, idp=None, **form_options())


@bp.route("/uploads/<path:filename>")
def uploaded(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
