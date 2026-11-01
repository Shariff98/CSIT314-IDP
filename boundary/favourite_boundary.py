"""Boundary: the Save / Remove buttons on IDPDetailPage (US-19, US-56) and FavouritesPage (US-44, US-08)."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from boundary.common import current_user_id, role_required
from control.remove_favourite_controller import RemoveFavouriteController
from control.save_favourite_controller import SaveFavouriteController
from control.search_category_controller import SearchCategoryController
from control.search_favourites_controller import SearchFavouritesController
from control.view_favourites_controller import ViewFavouritesController

bp = Blueprint("favourite", __name__)
customer_only = role_required("Customer")

MESSAGES = {"saved": "Saved to your favourites.", "already_saved": "Already in your favourites.",
            "removed": "Removed from your favourites.", "not_saved": "That project wasn't in your favourites."}


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
