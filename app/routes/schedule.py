from flask import Blueprint, render_template, session

from ..decorators import login_required
from ..db import fetch_all

schedule_bp = Blueprint("schedule", __name__, url_prefix="/schedule")


@schedule_bp.route("/", methods=["GET"])
@login_required
def schedule():
    username = session.get("username")
    role = session.get("role")

    # ADMIN → voit tout
    if role == "admin":
        rows = fetch_all(
            """
            SELECT subject, day, start_time, end_time
            FROM class_students
            ORDER BY day, start_time
            """
        )

    # STUDENT → voit uniquement ses cours
    else:
        rows = fetch_all(
            """
            SELECT subject, day, start_time, end_time
            FROM class_students
            WHERE student_name=%s
            ORDER BY day, start_time
            """,
            (username,),
        )

    return render_template("schedule.html", rows=rows)