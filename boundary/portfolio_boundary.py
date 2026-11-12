"""Boundary for the designer's own portfolio: MyIDPsPage (US-16, US-03), MyIDPDetailPage (US-27),
EditIDPPage (US-04, US-26) and the buttons for delete (US-05), status (US-06), publish (US-33)
and photos (US-55)."""
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for

from boundary.common import (api_error, api_role_required, as_text, current_user_id, json_body, role_required,
                             uploaded_file)
from boundary.idp_boundary import form_options
from boundary.project_serializer import owner_project_json, project_json
from control.search_category_controller import SearchCategoryController
from control.assign_idp_tags_controller import AssignIDPTagsController
from control.create_idp_controller import CreateIDPController
from control.delete_idp_controller import DeleteIDPController
from control.list_my_idps_controller import ListMyIDPsController
from control.mark_idp_status_controller import MarkIDPStatusController
from control.publish_idp_controller import PublishIDPController
from control.search_my_idps_controller import STATUS_FILTERS, SearchMyIDPsController
from control.update_idp_controller import UpdateIDPController
from control.upload_idp_photo_controller import UploadIDPPhotoController
from control.view_my_idp_controller import ViewMyIDPController

bp = Blueprint("portfolio", __name__, url_prefix="/my")
api_bp = Blueprint("portfolio_api", __name__, url_prefix="/api/designer")
designer_only = role_required("InteriorDesigner")
SEARCH_FIELDS = ("q", "status", "category", "date_from", "date_to")


api_designer_required = api_role_required("InteriorDesigner")


@api_bp.route("/portfolio", methods=["GET"])
@api_designer_required
def api_my_portfolio():
    args = request.args
    try:
        category = args.get("category")
        # Own projects can retain suspended categories, so allow all existing categories.
        if category and not any(row["category"].name == category for row in SearchCategoryController().search()):
            raise ValueError("Unknown category filter")
        if any(args.get(field) for field in SEARCH_FIELDS):
            projects = SearchMyIDPsController().search(current_user_id(), *(args.get(field) for field in SEARCH_FIELDS))
        else:
            projects = ListMyIDPsController().list_idps(current_user_id())
    except ValueError as error:
        return jsonify(error={"code": "invalid_request", "message": str(error)}), 400
    return jsonify(data={"items": [project_json(project) for project in projects], "total": len(projects)})


@api_bp.route("/portfolio", methods=["POST"])
@api_designer_required
def api_create_portfolio():
    try:
        payload = request.get_json(silent=True) if request.is_json else None
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        allowed = {"title", "description", "category", "budget", "property_type", "location",
                   "completion_date", "style_tags", "publish"}
        if set(payload) - allowed:
            raise ValueError("Only project metadata fields are accepted; ownership and generated fields cannot be supplied.")
        for field in ("title", "description", "category"):
            if not isinstance(payload.get(field), str) or not payload[field].strip():
                raise ValueError(f"{field} must be a nonempty string")
        for field in ("property_type", "location", "style_tags"):
            if field in payload and not isinstance(payload[field], str):
                raise ValueError(f"{field} must be a string")
        if payload.get("completion_date") is not None and not isinstance(payload["completion_date"], str):
            raise ValueError("completion_date must be a date string")
        if type(payload.get("budget")) is not int:
            raise ValueError("Budget must be a positive whole number")
        if payload["budget"] > 9223372036854775807:
            raise ValueError("Budget is too large")
        if type(payload.get("publish", False)) is not bool:
            raise ValueError("publish must be a JSON boolean")
        project = CreateIDPController().create_idp(
            current_user_id(), payload["title"], payload["description"], payload["category"], payload["budget"],
            payload.get("property_type", ""), payload.get("location", ""), payload.get("completion_date"),
            payload.get("style_tags", ""), publish=payload.get("publish", False))
    except ValueError as error:
        return jsonify(error={"code": "invalid_request", "message": str(error)}), 400
    return jsonify(data={"project": project_json(project)}), 201


# ---------- JSON API for the React "My project" page ----------
# Each route calls exactly one controller, like the HTML routes below. Someone else's
# project is reported as 404 (LookupError), bad input as 400 (ValueError).

def _api_call(action, status=200):
    try:
        data = action()
    except LookupError:
        return api_error("not_found", "Project not found.", 404)
    except ValueError as error:
        return api_error("invalid_request", str(error), 400)
    return jsonify(data=data), status


def _my_project(idp_id):
    idp = ViewMyIDPController().view(current_user_id(), idp_id)
    if idp is None:
        raise LookupError("Project not found")
    return {"project": owner_project_json(idp)}


@api_bp.route("/portfolio/<int:idp_id>", methods=["GET"])
@api_designer_required
def api_my_project(idp_id):
    """US-27 View my IDP details (drafts included, not counted as a view)."""
    return _api_call(lambda: _my_project(idp_id))


@api_bp.route("/portfolio/<int:idp_id>", methods=["PUT"])
@api_designer_required
def api_update_project(idp_id):
    """US-04 Update IDP."""
    def update():
        p = json_body()
        for field in ("title", "description", "category", "property_type", "location", "completion_date"):
            if p.get(field) is not None and not isinstance(p[field], str):
                raise ValueError(f"{field} must be text")
        UpdateIDPController().update_idp(
            current_user_id(), idp_id, p.get("title"), p.get("description"), p.get("category"),
            as_text(p.get("budget")), p.get("property_type") or "", p.get("location") or "",
            p.get("completion_date") or None)
        return _my_project(idp_id)
    return _api_call(update)


@api_bp.route("/portfolio/<int:idp_id>", methods=["DELETE"])
@api_designer_required
def api_delete_project(idp_id):
    """US-05 Delete IDP (its photos, favourites and views go with it)."""
    def delete():
        if DeleteIDPController().delete(current_user_id(), idp_id) == "not_found":
            raise LookupError("Project not found")
        return {"project_id": idp_id, "deleted": True}
    return _api_call(delete)


@api_bp.route("/portfolio/<int:idp_id>/tags", methods=["PUT"])
@api_designer_required
def api_assign_tags(idp_id):
    """US-26 Assign category and style tags. style_tags may be "a, b" or ["a", "b"]."""
    def assign():
        p = json_body()
        AssignIDPTagsController().assign(current_user_id(), idp_id, p.get("category"), as_text(p.get("style_tags")) or "")
        return _my_project(idp_id)
    return _api_call(assign)


@api_bp.route("/portfolio/<int:idp_id>/status", methods=["PUT"])
@api_designer_required
def api_mark_status(idp_id):
    """US-06 Mark IDP as Current or Past."""
    def mark():
        MarkIDPStatusController().mark(current_user_id(), idp_id, json_body().get("status"))
        return _my_project(idp_id)
    return _api_call(mark)


@api_bp.route("/portfolio/<int:idp_id>/publish", methods=["PUT"])
@api_designer_required
def api_publish(idp_id):
    """US-33 Publish ({"published": true}) or move back to drafts ({"published": false})."""
    def publish():
        wanted = json_body().get("published")
        if type(wanted) is not bool:
            raise ValueError("published must be true or false")
        controller = PublishIDPController()
        result = (controller.publish if wanted else controller.unpublish)(current_user_id(), idp_id)
        return {**_my_project(idp_id), "result": result}
    return _api_call(publish)


@api_bp.route("/portfolio/<int:idp_id>/photos", methods=["POST"])
@api_designer_required
def api_upload_photo(idp_id):
    """US-55 Upload one photo (multipart field "photo"). The first photo becomes the cover."""
    def upload():
        filename, data = uploaded_file("photo")
        if not filename:
            raise ValueError("Choose a photo to upload")
        UploadIDPPhotoController().upload(current_user_id(), idp_id, filename, data)
        return _my_project(idp_id)
    return _api_call(upload, 201)


@api_bp.route("/photos/<int:photo_id>/cover", methods=["PUT"])
@api_designer_required
def api_set_cover(photo_id):
    """US-55 Set a photo as the project's cover image."""
    return _api_call(lambda: _my_project(UploadIDPPhotoController().set_cover(current_user_id(), photo_id).idp_id))


@api_bp.route("/photos/<int:photo_id>", methods=["DELETE"])
@api_designer_required
def api_delete_photo(photo_id):
    """US-55 Delete a photo. If it was the cover, the next photo becomes the cover."""
    return _api_call(lambda: _my_project(UploadIDPPhotoController().delete_photo(current_user_id(), photo_id)))


@bp.route("/idps")
@designer_only
def my_idps():
    a = request.args
    try:
        if any(a.get(k) for k in SEARCH_FIELDS):
            idps = SearchMyIDPsController().search(current_user_id(), *(a.get(k) for k in SEARCH_FIELDS))
        else:
            idps = ListMyIDPsController().list_idps(current_user_id())
    except ValueError as error:
        flash(str(error), "danger")
        idps = []
    return render_template("portfolio/list.html", idps=idps, args=a, statuses=STATUS_FILTERS, **form_options())


@bp.route("/idps/<int:idp_id>")
@designer_only
def my_idp(idp_id):
    idp = ViewMyIDPController().view(current_user_id(), idp_id)
    if idp is None:
        abort(404)
    return render_template("portfolio/detail.html", idp=idp, **form_options())


@bp.route("/idps/<int:idp_id>/edit", methods=["GET", "POST"])
@designer_only
def edit(idp_id):
    idp = ViewMyIDPController().view(current_user_id(), idp_id)
    if idp is None:
        abort(404)
    if request.method == "POST":
        f = request.form
        try:
            UpdateIDPController().update_idp(current_user_id(), idp_id, f.get("title"), f.get("description"),
                                             f.get("category"), f.get("budget"), f.get("property_type"),
                                             f.get("location"), f.get("completion_date"))
        except ValueError as error:
            flash(str(error), "danger")
            return render_template("idp_form.html", form=f, idp=idp, **form_options()), 400
        flash("Project updated.", "success")
        return redirect(url_for("portfolio.my_idp", idp_id=idp_id))
    return render_template("idp_form.html", form=vars(idp), idp=idp, **form_options())


def _action(idp_id, action, success):
    """Runs one portfolio action and returns to the project page with a message."""
    try:
        result = action()
    except LookupError:
        abort(404)
    except ValueError as error:
        flash(str(error), "danger")
    else:
        flash(success(result) if callable(success) else success, "success")
    return redirect(url_for("portfolio.my_idp", idp_id=idp_id))


@bp.route("/idps/<int:idp_id>/tags", methods=["POST"])
@designer_only
def tags(idp_id):
    f = request.form
    return _action(idp_id, lambda: AssignIDPTagsController().assign(current_user_id(), idp_id, f.get("category"),
                                                                    f.get("style_tags")),
                   "Category and style tags saved.")


@bp.route("/idps/<int:idp_id>/status", methods=["POST"])
@designer_only
def status(idp_id):
    return _action(idp_id, lambda: MarkIDPStatusController().mark(current_user_id(), idp_id,
                                                                  request.form.get("status")),
                   lambda idp: f"Marked as {idp.status.lower()}.")


@bp.route("/idps/<int:idp_id>/publish", methods=["POST"])
@designer_only
def publish(idp_id):
    controller = PublishIDPController()
    if request.form.get("action") == "unpublish":
        return _action(idp_id, lambda: controller.unpublish(current_user_id(), idp_id),
                       lambda r: "Project moved back to drafts." if r == "unpublished" else "Already a draft.")
    return _action(idp_id, lambda: controller.publish(current_user_id(), idp_id),
                   lambda r: "Project published." if r == "published" else "Already published.")


@bp.route("/idps/<int:idp_id>/delete", methods=["POST"])
@designer_only
def delete(idp_id):
    if DeleteIDPController().delete(current_user_id(), idp_id) == "not_found":
        abort(404)
    flash("Project deleted.", "success")
    return redirect(url_for("portfolio.my_idps"))


@bp.route("/idps/<int:idp_id>/photos", methods=["POST"])
@designer_only
def upload_photo(idp_id):
    filename, data = uploaded_file("photo")
    return _action(idp_id, lambda: UploadIDPPhotoController().upload(current_user_id(), idp_id, filename or "", data),
                   "Photo uploaded.")


@bp.route("/photos/<int:photo_id>/<action>", methods=["POST"])
@designer_only
def photo_action(photo_id, action):
    controller = UploadIDPPhotoController()
    try:
        if action == "cover":
            idp_id = controller.set_cover(current_user_id(), photo_id).idp_id
            flash("Cover image set.", "success")
        elif action == "delete":
            idp_id = controller.delete_photo(current_user_id(), photo_id)
            flash("Photo deleted.", "success")
        else:
            abort(404)
    except LookupError:
        abort(404)
    return redirect(url_for("portfolio.my_idp", idp_id=idp_id))
