import logging

from flask import Blueprint, flash, redirect, render_template, request, session

from ..decorators import login_required, role_required
from ..db import execute, fetch_all, fetch_one
from ..forms import CreateAssessmentForm, CreateHomeworkForm, CsrfForm, RecordAbsenceForm
from ..security import decrypt_value, encrypt_value

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")
logger = logging.getLogger(__name__)


@teacher_bp.route("/dashboard", methods=["GET"])
@login_required
@role_required("PROFESSOR")
def dashboard():
    teacher_id = session.get("user_id")
    teacher_id = teacher_id if teacher_id else None
    classes = fetch_all(
        """
        SELECT c.id, c.name
        FROM classes c
        WHERE c.teacher_id=%s
        ORDER BY c.id DESC
        """,
        (teacher_id,),
    )
    return render_template(
        "teacher_dashboard.html",
        classes=classes,
        form_assessment=CreateAssessmentForm(),
        form_homework=CreateHomeworkForm(),
        form_absence=RecordAbsenceForm(),
    )


@teacher_bp.route("/classes/<int:class_id>/homeworks/create", methods=["POST"])
@login_required
@role_required("PROFESSOR")
def create_homework(class_id: int):
    form = CreateHomeworkForm()
    if not form.validate_on_submit():
        flash("Données devoir invalides.", "error")
        return redirect("/teacher/dashboard")

    teacher_id = session.get("user_id")
    row = fetch_one("SELECT id FROM classes WHERE id=%s AND teacher_id=%s", (class_id, teacher_id))
    if not row:
        return render_template("unauthorized.html"), 403

    execute(
        """
        INSERT INTO homeworks(class_id, title, description, due_date, created_by)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            class_id,
            form.title.data,
            form.description.data if form.description.data else None,
            form.due_date.data if form.due_date.data else None,
            teacher_id,
        ),
    )
    flash("Devoir créé.", "success")
    return redirect("/teacher/dashboard")


@teacher_bp.route("/classes/<int:class_id>/absences/record", methods=["POST"])
@login_required
@role_required("PROFESSOR")
def record_absence(class_id: int):
    form = RecordAbsenceForm()
    if not form.validate_on_submit():
        flash("Données absence invalides.", "error")
        return redirect("/teacher/dashboard")

    teacher_id = session.get("user_id")
    row = fetch_one("SELECT id FROM classes WHERE id=%s AND teacher_id=%s", (class_id, teacher_id))
    if not row:
        return render_template("unauthorized.html"), 403

    st = fetch_one(
        """
        SELECT u.id
        FROM class_students cs
        JOIN users u ON u.id=cs.student_id
        WHERE cs.class_id=%s AND u.username=%s AND u.role='STUDENT'
        """,
        (class_id, form.student_username.data),
    )
    if not st:
        flash("Étudiant introuvable dans cette classe.", "error")
        return redirect("/teacher/dashboard")

    execute(
        """
        INSERT INTO absences(class_id, student_id, absence_date, reason, recorded_by)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
          reason=VALUES(reason),
          recorded_by=VALUES(recorded_by)
        """,
        (class_id, st["id"], form.absence_date.data, form.reason.data if form.reason.data else None, teacher_id),
    )
    flash("Absence enregistrée.", "success")
    return redirect("/teacher/dashboard")


@teacher_bp.route("/classes/<int:class_id>/assessments/create", methods=["POST"])
@login_required
@role_required("PROFESSOR")
def create_assessment(class_id: int):
    form = CreateAssessmentForm()
    if not form.validate_on_submit():
        flash("Données évaluation invalides.", "error")
        return redirect("/teacher/dashboard")

    teacher_id = session.get("user_id")
    row = fetch_one(
        "SELECT id FROM classes WHERE id=%s AND teacher_id=%s",
        (class_id, teacher_id),
    )
    if not row:
        logger.warning(
            "Unauthorized horizontal access (teacher create assessment denied). teacher_id=%s class_id=%s remote=%s path=%s",
            teacher_id,
            class_id,
            request.remote_addr,
            request.path,
        )
        return render_template("unauthorized.html"), 403

    execute(
        """
        INSERT INTO assessments(class_id, title, due_date, created_by)
        VALUES (%s, %s, %s, %s)
        """,
        (class_id, form.title.data, form.due_date.data if form.due_date.data else None, teacher_id),
    )
    return redirect(f"/teacher/assessments/by-class/{class_id}")


@teacher_bp.route("/assessments/by-class/<int:class_id>", methods=["GET"])
@login_required
@role_required("PROFESSOR")
def list_assessments_by_class(class_id: int):
    teacher_id = session.get("user_id")
    # Sécurité horizontale : s'assurer que la classe appartient au professeur.
    row = fetch_one("SELECT id FROM classes WHERE id=%s AND teacher_id=%s", (class_id, teacher_id))
    if not row:
        logger.warning(
            "Unauthorized horizontal access (teacher list assessments denied). teacher_id=%s class_id=%s remote=%s path=%s",
            teacher_id,
            class_id,
            request.remote_addr,
            request.path,
        )
        return render_template("unauthorized.html"), 403

    assessments = fetch_all(
        "SELECT id, title, due_date FROM assessments WHERE class_id=%s ORDER BY id DESC",
        (class_id,),
    )
    return render_template(
        "teacher_assessments.html",
        class_id=class_id,
        assessments=assessments,
        create_form=CreateAssessmentForm(),
    )


@teacher_bp.route("/assessments/<int:assessment_id>", methods=["GET", "POST"])
@login_required
@role_required("PROFESSOR")
def assessment_grades(assessment_id: int):
    teacher_id = session.get("user_id")
    assessment = fetch_one(
        """
        SELECT a.id, a.title, a.class_id, a.due_date
        FROM assessments a
        JOIN classes c ON c.id=a.class_id
        WHERE a.id=%s AND c.teacher_id=%s
        """,
        (assessment_id, teacher_id),
    )
    if not assessment:
        logger.warning(
            "Unauthorized horizontal access (teacher edit grades denied). teacher_id=%s assessment_id=%s remote=%s path=%s",
            teacher_id,
            assessment_id,
            request.remote_addr,
            request.path,
        )
        return render_template("unauthorized.html"), 403

    students = fetch_all(
        """
        SELECT u.id, u.username
        FROM class_students cs
        JOIN users u ON u.id=cs.student_id
        WHERE cs.class_id=%s AND u.role='STUDENT'
        ORDER BY u.username
        """,
        (assessment["class_id"],),
    )

    csrf_form = CsrfForm()

    if request.method == "POST":
        try:
            # Le CSRF est validé par Flask-WTF si hidden_tag présent.
            csrf_form.validate_on_submit()
        except Exception:
            # En cas d'échec CSRF, on renvoie un 403 générique.
            return render_template("unauthorized.html"), 403

        for st in students:
            field_name = f"grade_{st['id']}"
            raw = request.form.get(field_name, "").strip()
            if raw == "":
                continue
            try:
                grade = float(raw.replace(",", "."))
            except ValueError:
                flash("Valeur de note invalide.", "error")
                continue
            if grade < 0 or grade > 20:
                flash("Note hors plage (0-20).", "error")
                continue
            execute(
                """
                INSERT INTO grades(assessment_id, student_id, grade_encrypted, updated_by)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  grade_encrypted=VALUES(grade_encrypted),
                  updated_by=VALUES(updated_by)
                """,
                (assessment_id, st["id"], encrypt_value(str(grade)), teacher_id),
            )
        return redirect(f"/teacher/assessments/{assessment_id}")

    # GET : charger les notes existantes (décryptées)
    existing = fetch_all(
        """
        SELECT student_id, grade_encrypted
        FROM grades
        WHERE assessment_id=%s
        """,
        (assessment_id,),
    )
    grade_map = {row["student_id"]: decrypt_value(row["grade_encrypted"]) for row in existing}

    return render_template(
        "teacher_assessment_grades.html",
        assessment=assessment,
        students=students,
        grade_map=grade_map,
        csrf_form=csrf_form,
    )

