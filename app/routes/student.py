from flask import Blueprint, render_template, session

from ..decorators import login_required, role_required
from ..db import fetch_all
from ..security import decrypt_value

student_bp = Blueprint("student", __name__, url_prefix="/student")


@student_bp.route("/dashboard", methods=["GET"])
@login_required
@role_required("STUDENT")
def dashboard():
    student_id = session.get("user_id")
    grades = fetch_all(
        """
        SELECT a.id AS assessment_id, a.title, a.due_date, g.grade_encrypted
        FROM grades g
        JOIN assessments a ON a.id=g.assessment_id
        WHERE g.student_id=%s
        ORDER BY a.due_date DESC, a.id DESC
        """,
        (student_id,),
    )
    grade_list = [
        {
            "assessment_id": row["assessment_id"],
            "title": row["title"],
            "due_date": row["due_date"],
            "grade": decrypt_value(row["grade_encrypted"]),
        }
        for row in grades
    ]

    schedule = fetch_all(
        """
        SELECT s.id, c.name AS class_name, s.day_of_week, s.start_time, s.end_time, s.location
        FROM class_students cs
        JOIN schedules s ON s.class_id=cs.class_id
        JOIN classes c ON c.id=s.class_id
        WHERE cs.student_id=%s
        ORDER BY c.id DESC, s.day_of_week ASC, s.start_time ASC
        """,
        (student_id,),
    )

    homeworks = fetch_all(
        """
        SELECT h.id, c.name AS class_name, h.title, h.description, h.due_date, h.created_at
        FROM class_students cs
        JOIN homeworks h ON h.class_id=cs.class_id
        JOIN classes c ON c.id=h.class_id
        WHERE cs.student_id=%s
        ORDER BY (h.due_date IS NULL), h.due_date ASC, h.id DESC
        """,
        (student_id,),
    )

    absences = fetch_all(
        """
        SELECT a.id, c.name AS class_name, a.absence_date, a.reason, a.created_at
        FROM absences a
        JOIN classes c ON c.id=a.class_id
        WHERE a.student_id=%s
        ORDER BY a.absence_date DESC, a.id DESC
        """,
        (student_id,),
    )

    blackjack_history = fetch_all(
        """
        SELECT score, result, created_at
        FROM blackjack_history
        WHERE student_id=%s
        ORDER BY created_at DESC, id DESC
        LIMIT 20
        """,
        (student_id,),
    )

    return render_template(
        "student_dashboard.html",
        grades=grade_list,
        schedule=schedule,
        homeworks=homeworks,
        absences=absences,
        blackjack_history=blackjack_history,
    )

