"""Boundary for the designer's own portfolio: MyIDPsPage (US-16, US-03), MyIDPDetailPage (US-27),
EditIDPPage (US-04, US-26) and the buttons for delete (US-05), status (US-06), publish (US-33)
and photos (US-55)."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from boundary.common import current_user_id, role_required, uploaded_file
from boundary.idp_boundary import form_options
from control.assign_idp_tags_controller import AssignIDPTagsController
from control.delete_idp_controller import DeleteIDPController
from control.list_my_idps_controller import ListMyIDPsController
from control.mark_idp_status_controller import MarkIDPStatusController
from control.publish_idp_controller import PublishIDPController
from control.search_my_idps_controller import STATUS_FILTERS, SearchMyIDPsController
from control.update_idp_controller import UpdateIDPController
from control.upload_idp_photo_controller import UploadIDPPhotoController
from control.view_my_idp_controller import ViewMyIDPController

bp = Blueprint("portfolio", __name__, url_prefix="/my")
designer_only = role_required("InteriorDesigner")
SEARCH_FIELDS = ("q", "status", "category", "date_from", "date_to")


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
