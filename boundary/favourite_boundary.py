"""Boundary: the Save / Remove buttons on IDPDetailPage (US-19, US-56) and FavouritesPage (US-44, US-08)."""
from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for

from boundary.common import api_role_required, current_user_id, role_required
from boundary.project_serializer import project_json
from control.remove_favourite_controller import RemoveFavouriteController
from control.save_favourite_controller import SaveFavouriteController
from control.search_category_controller import SearchCategoryController
from control.search_favourites_controller import SearchFavouritesController
from control.view_favourites_controller import ViewFavouritesController

bp = Blueprint("favourite", __name__)
customer_only = role_required("Customer")

MESSAGES = {"saved": "Saved to your favourites.", "already_saved": "Already in your favourites.",
            "removed": "Removed from your favourites.", "not_saved": "That project wasn't in your favourites."}


api_customer_required = api_role_required("Customer")


@bp.route("/api/favourites/projects/<int:idp_id>", methods=["POST"])
@api_customer_required
def api_save(idp_id):
    result = SaveFavouriteController().save(current_user_id(), idp_id)
    if result == "not_found":
        return jsonify(error={"code": "not_found", "message": "Project not found or unavailable."}), 404
    return jsonify(data={"project_id": idp_id, "saved": True, "result": result})


@bp.route("/api/favourites/projects/<int:idp_id>", methods=["DELETE"])
@api_customer_required
def api_remove(idp_id):
    result = RemoveFavouriteController().remove(current_user_id(), idp_id)
    return jsonify(data={"project_id": idp_id, "saved": False, "result": result})


@bp.route("/api/favourites/projects", methods=["GET"])
@api_customer_required
def api_favourites():
    args = request.args
    if args.get("q") or args.get("category"):
        items = SearchFavouritesController().search(current_user_id(), args.get("q", ""), args.get("category"))
    else:
        items = ViewFavouritesController().list_favourites(current_user_id())
    # Previously saved projects may since have been unpublished.
    published = [item for item in items if item.is_published]
    return jsonify(data={"items": [project_json(item) for item in published], "total": len(published)})


@bp.route("/idp/<int:idp_id>/save", methods=["POST"])
@customer_only
def save(idp_id):
    result = SaveFavouriteController().save(current_user_id(), idp_id)
    if result == "not_found":
        abort(404)
    flash(MESSAGES[result], "success")
    return redirect(url_for("idp.detail", idp_id=idp_id))


@bp.route("/idp/<int:idp_id>/unsave", methods=["POST"])
@customer_only
def remove(idp_id):
    result = RemoveFavouriteController().remove(current_user_id(), idp_id)
    flash(MESSAGES[result], "success" if result == "removed" else "info")
    return redirect(request.form.get("next") or url_for("favourite.favourites"))


@bp.route("/favourites")
@customer_only
def favourites():
    a = request.args
    if a.get("q") or a.get("category"):
        items = SearchFavouritesController().search(current_user_id(), a.get("q", ""), a.get("category"))
    else:
        items = ViewFavouritesController().list_favourites(current_user_id())
    return render_template("favourites.html", items=items, args=a,
                           categories=SearchCategoryController().active_names())
