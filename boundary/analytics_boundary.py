"""Boundary for the designer's interest tracking pages (spec feature 5):
dashboard (US-57), view counts (US-29), shortlist counts (US-46), ranking (US-09), trends by date
range (US-35), segment filter (US-36), compare (US-58), CSV export (US-47), notifications (US-48)."""
from flask import Blueprint, Response, flash, jsonify, redirect, render_template, request, url_for

from boundary.common import api_role_required, current_user_id, role_required
from boundary.idp_boundary import form_options
from control.compare_idps_controller import CompareIDPsController
from control.export_interest_csv_controller import ExportInterestCSVController
from control.filter_analytics_controller import FilterAnalyticsController
from control.list_my_idps_controller import ListMyIDPsController
from control.notify_milestone_controller import NotifyMilestoneController
from control.portfolio_dashboard_controller import PortfolioDashboardController
from control.rank_idps_controller import RankIDPsController
from control.view_idp_view_count_controller import ViewIDPViewCountController
from control.view_interest_by_date_range_controller import ViewInterestByDateRangeController
from control.view_shortlist_count_controller import ViewShortlistCountController

bp = Blueprint("analytics", __name__, url_prefix="/analytics")
api_bp = Blueprint("analytics_api", __name__, url_prefix="/api/designer")
designer_only = role_required("InteriorDesigner")


@api_bp.route("/analytics")
@api_role_required("InteriorDesigner")
def api_dashboard():
    """The React designer dashboard: summary (US-57), views per project (US-29),
    shortlists per project (US-46) and the latest milestone notifications (US-48).
    The deeper reports (rank, trend, compare, CSV) stay on the /analytics pages."""
    designer_id = current_user_id()
    summary = PortfolioDashboardController().summary(designer_id)
    top = summary.pop("top_project")
    summary["top_project"] = {"id": top.id, "title": top.title, "views": top.views} if top else None

    def rows(data, metric):
        return [{"id": r["idp"].id, "title": r["idp"].title, "published": r["idp"].is_published,
                 "status": r["idp"].status, metric: r[metric]} for r in data["rows"]]

    views = ViewIDPViewCountController().view_counts(designer_id)
    shortlists = ViewShortlistCountController().shortlist_counts(designer_id)
    notifier = NotifyMilestoneController()
    latest = notifier.list_notifications(designer_id)[:5]
    return jsonify(data={
        "summary": summary,
        "views": {"total": views["total"], "rows": rows(views, "views")},
        "shortlists": {"total": shortlists["total"], "rows": rows(shortlists, "shortlists")},
        "notifications": [{"id": n.id, "idp_id": n.idp_id, "message": n.message, "is_read": bool(n.is_read),
                           "created_at": n.created_at} for n in latest],
        "unread_notifications": notifier.unread_count(designer_id),
    })


@bp.route("/")
@designer_only
def dashboard():
    return render_template("analytics/dashboard.html", summary=PortfolioDashboardController().summary(current_user_id()))


@bp.route("/views")
@designer_only
def views():
    data = ViewIDPViewCountController().view_counts(current_user_id())
    return render_template("analytics/counts.html", data=data, metric="views", title="Views per project")


@bp.route("/shortlists")
@designer_only
def shortlists():
    data = ViewShortlistCountController().shortlist_counts(current_user_id())
    return render_template("analytics/counts.html", data=data, metric="shortlists", title="Shortlists per project")


@bp.route("/rank")
@designer_only
def rank():
    metric = request.args.get("by", "views")
    try:
        rows = RankIDPsController().rank(current_user_id(), metric)
    except ValueError as error:
        flash(str(error), "danger")
        return redirect(url_for("analytics.rank"))
    return render_template("analytics/rank.html", rows=rows, metric=metric)


@bp.route("/trend")
@designer_only
def trend():
    a = request.args
    try:
        data = ViewInterestByDateRangeController().trend(current_user_id(), a.get("period", "daily"),
                                                         a.get("start"), a.get("end"))
    except ValueError as error:
        flash(str(error), "danger")
        data = ViewInterestByDateRangeController().trend(current_user_id())
    peak = max([r["views"] for r in data["rows"]] + [1])
    return render_template("analytics/trend.html", data=data, peak=peak)


@bp.route("/segment")
@designer_only
def segment():
    a = request.args
    try:
        data = FilterAnalyticsController().filter(current_user_id(), a.get("category"), a.get("status"))
    except ValueError as error:
        flash(str(error), "danger")
        data = FilterAnalyticsController().filter(current_user_id())
    return render_template("analytics/segment.html", data=data, args=a, **form_options())


@bp.route("/compare")
@designer_only
def compare():
    chosen = request.args.getlist("idp")
    result = None
    if chosen:
        try:
            result = CompareIDPsController().compare(current_user_id(), chosen)
        except (ValueError, LookupError) as error:
            flash(str(error), "danger")
    return render_template("analytics/compare.html", result=result, chosen=chosen,
                           idps=ListMyIDPsController().list_idps(current_user_id()))


@bp.route("/export.csv")
@designer_only
def export_csv():
    csv_text = ExportInterestCSVController().export(current_user_id())
    return Response(csv_text, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=interest-statistics.csv"})


@bp.route("/notifications", methods=["GET", "POST"])
@designer_only
def notifications():
    controller = NotifyMilestoneController()
    if request.method == "POST":
        controller.mark_all_read(current_user_id())
        return redirect(url_for("analytics.notifications"))
    return render_template("analytics/notifications.html",
                           notifications=controller.list_notifications(current_user_id()))


@bp.app_context_processor
def unread_notifications():
    """Puts the designer's unread notification count in every page's navigation bar."""
    from flask import session
    if session.get("role") != "InteriorDesigner":
        return {}
    return {"unread_notifications": NotifyMilestoneController().unread_count(session["user_id"])}
