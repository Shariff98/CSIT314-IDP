"""Boundary for Platform Management (spec feature 6): dashboard (US-50), demand (US-20),
categories (US-49, 59, 38, 60) and daily / weekly / monthly reports (US-39, 10, 30) with export (US-40)."""
from flask import Blueprint, Response, abort, flash, redirect, render_template, request, url_for

from boundary.common import role_required
from control.create_category_controller import CreateCategoryController
from control.export_report_controller import ExportReportController
from control.generate_daily_report_controller import GenerateDailyReportController
from control.generate_monthly_report_controller import GenerateMonthlyReportController
from control.generate_weekly_report_controller import GenerateWeeklyReportController
from control.platform_dashboard_controller import PlatformDashboardController
from control.search_category_controller import SearchCategoryController
from control.suspend_category_controller import SuspendCategoryController
from control.update_category_controller import UpdateCategoryController
from control.view_top_categories_controller import ViewTopCategoriesController

bp = Blueprint("platform", __name__, url_prefix="/platform")
manager_only = role_required("PlatformManager")
REPORTS = {"daily": GenerateDailyReportController, "weekly": GenerateWeeklyReportController,
           "monthly": GenerateMonthlyReportController}


@bp.route("/")
@manager_only
def dashboard():
    return render_template("platform/dashboard.html", data=PlatformDashboardController().metrics())


@bp.route("/demand")
@manager_only
def demand():
    return render_template("platform/demand.html", data=ViewTopCategoriesController().view())


# ---------- categories ----------
@bp.route("/categories")
@manager_only
def categories():
    a = request.args
    controller = SearchCategoryController()
    return render_template("platform/categories.html", rows=controller.search(a.get("q", ""), a.get("status")),
                           active=controller.active_names(), args=a)


@bp.route("/categories/new", methods=["GET", "POST"])
@manager_only
def create_category():
    if request.method == "POST":
        f = request.form
        try:
            CreateCategoryController().create_category(f.get("name"), f.get("description"))
        except ValueError as error:
            flash(str(error), "danger")
            return render_template("platform/category_form.html", form=f, category=None), 400
        flash("Category created.", "success")
        return redirect(url_for("platform.categories"))
    return render_template("platform/category_form.html", form={}, category=None)


@bp.route("/categories/<int:category_id>/edit", methods=["GET", "POST"])
@manager_only
def edit_category(category_id):
    category = SearchCategoryController().view(category_id)
    if category is None:
        abort(404)
    if request.method == "POST":
        f = request.form
        try:
            UpdateCategoryController().update_category(category_id, f.get("name"), f.get("description"))
        except ValueError as error:
            flash(str(error), "danger")
            return render_template("platform/category_form.html", form=f, category=category), 400
        flash("Category updated.", "success")
        return redirect(url_for("platform.categories"))
    return render_template("platform/category_form.html", form=vars(category), category=category)


@bp.route("/categories/<int:category_id>/<action>", methods=["POST"])
@manager_only
def change_category(category_id, action):
    controller = SuspendCategoryController()
    reassign_to = request.form.get("reassign_to")
    try:
        if action == "suspend":
            moved = controller.suspend(category_id, reassign_to)
            flash(f"Category suspended. {moved} projects moved to {reassign_to}." if moved
                  else "Category suspended.", "success")
        elif action == "delete":
            moved = controller.delete(category_id, reassign_to)
            flash(f"Category deleted. {moved} projects moved to {reassign_to}." if moved
                  else "Category deleted.", "success")
        elif action == "reactivate":
            controller.reactivate(category_id)
            flash("Category reactivated.", "success")
        else:
            abort(404)
    except LookupError:
        abort(404)
    except ValueError as error:
        flash(str(error), "danger")
    return redirect(url_for("platform.categories"))


# ---------- reports ----------
@bp.route("/reports/<period>")
@manager_only
def report(period):
    if period not in REPORTS:
        abort(404)
    try:
        result = REPORTS[period]().generate(request.args.get("date"))
    except ValueError as error:
        flash(str(error), "danger")
        result = REPORTS[period]().generate()
    return render_template("platform/report.html", report=result, period=period)


@bp.route("/reports/<period>/export")
@manager_only
def export_report(period):
    try:
        filename, mime, data = ExportReportController().export(period, request.args.get("date"),
                                                               request.args.get("format", "csv"))
    except ValueError as error:
        flash(str(error), "danger")
        return redirect(url_for("platform.report", period=period if period in REPORTS else "daily"))
    return Response(data, mimetype=mime, headers={"Content-Disposition": f"attachment; filename={filename}"})
