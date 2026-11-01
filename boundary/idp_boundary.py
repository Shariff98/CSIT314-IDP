"""Boundary: SearchIDPPage (US-07 browse, US-28 search, US-17 filter, US-18 sort),
IDPDetailPage (US-34, US-37, US-45) and CreateIDPPage (US-54)."""
import uuid

from flask import (Blueprint, abort, current_app, flash, redirect, render_template, request,
                   send_from_directory, session, url_for)

from boundary.common import current_user_id, role_required
from control.browse_idp_controller import SORT_OPTIONS, BrowseIDPController
from control.create_idp_controller import CreateIDPController
from control.filter_idp_controller import FilterIDPController
from control.ownership import PROPERTY_TYPES, STYLES
from control.save_favourite_controller import SaveFavouriteController
from control.search_category_controller import SearchCategoryController
from control.search_idp_controller import SearchIDPController
from control.view_designer_projects_controller import ViewDesignerProjectsController
from control.view_idp_controller import ViewIDPController

bp = Blueprint("idp", __name__)

FILTERS = ("category", "style", "min_budget", "max_budget", "property_type", "location")


def form_options():
    return {"categories": SearchCategoryController().active_names(), "property_types": PROPERTY_TYPES,
            "styles": STYLES, "sort_options": SORT_OPTIONS}


@bp.route("/")
def search():
    a = request.args
    keyword, sort = a.get("q", ""), a.get("sort", "newest")
    try:
        if any(a.get(name) for name in FILTERS):
            results = FilterIDPController().filter(keyword, *(a.get(name) for name in FILTERS), sort=sort)
        elif keyword.strip():
            results = SearchIDPController().search(keyword, sort)
        else:
            results = BrowseIDPController().browse(sort)
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
