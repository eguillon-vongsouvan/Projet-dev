import os

from flask import Blueprint, abort, current_app, redirect, render_template, send_file, session, url_for

from ..decorators import login_required

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def index():
    return render_template("home.html")


@main_bp.route("/health")
def health():
    return {"status": "ok"}


@main_bp.route("/media/dashboard-bg", methods=["GET"])
@login_required
def dashboard_bg():
    path = current_app.config.get("DASHBOARD_BG_PATH", "")
    if not path or not os.path.isfile(path):
        abort(404)
    return send_file(path)


# Les endpoints /dashboard-* sont conservés uniquement à titre de fallback pédagogique.

