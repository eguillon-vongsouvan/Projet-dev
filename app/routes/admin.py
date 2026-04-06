from flask import Blueprint, flash, redirect, render_template

from ..db import execute, fetch_all, fetch_one
from ..decorators import login_required, role_required
from ..forms import AssignStudentForm, CreateClassForm, CreateScheduleForm, CreateUserForm

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/", methods=["GET"])
@login_required
@role_required("ADMIN")
def dashboard():
    classes = fetch_all(
        """
        SELECT c.id, c.name, u.username AS teacher_username
        FROM classes c
        LEFT JOIN users u ON u.id = c.teacher_id
        ORDER BY c.id DESC
        """
    )
    users = fetch_all(
        """
        SELECT id, username, role, is_banned, created_at
        FROM users
        WHERE role <> 'LOVERBOY'
        ORDER BY created_at DESC
        """
    )
    teachers = fetch_all("SELECT id, username FROM users WHERE role='PROFESSOR' ORDER BY username")
    students = fetch_all("SELECT id, username FROM users WHERE role='STUDENT' ORDER BY username")

    form_user = CreateUserForm()
    form_class = CreateClassForm()
    # Formulaires dynamiques gérés par URL (class_id dans le chemin)

    return render_template(
        "admin_dashboard.html",
        classes=classes,
        teachers=teachers,
        students=students,
        users=users,
        form_user=form_user,
        form_class=form_class,
    )


@admin_bp.route("/users/create", methods=["POST"])
@login_required
@role_required("ADMIN")
def create_user():
    form = CreateUserForm()
    if not form.validate_on_submit():
        flash("Données utilisateur invalides.", "error")
        return redirect("/admin/")

    from ..security import hash_password  # import local pour réduire dépendances dans les routes

    execute(
        """
        INSERT INTO users(username, password_hash, role)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
          password_hash=VALUES(password_hash),
          role=VALUES(role)
        """,
        (form.username.data, hash_password(form.password.data), form.role.data),
    )
    flash("Compte créé.", "success")
    return redirect("/admin/")


@admin_bp.route("/users/<int:user_id>/toggle-ban", methods=["POST"])
@login_required
@role_required("ADMIN")
def toggle_ban(user_id: int):
    row = fetch_one("SELECT id, is_banned FROM users WHERE id=%s", (user_id,))
    if not row:
        flash("Utilisateur introuvable.", "error")
        return redirect("/admin/")
    new_val = 0 if row["is_banned"] else 1
    execute("UPDATE users SET is_banned=%s WHERE id=%s", (new_val, user_id))
    flash("Statut mis à jour.", "success")
    return redirect("/admin/")


@admin_bp.route("/classes/create", methods=["POST"])
@login_required
@role_required("ADMIN")
def create_class():
    form = CreateClassForm()
    if not form.validate_on_submit():
        flash("Données classe invalides.", "error")
        return redirect("/admin/")

    teacher_username = (form.teacher_username.data or "").strip()
    teacher_id = None
    if teacher_username:
        row = fetch_one("SELECT id FROM users WHERE username=%s AND role='PROFESSOR'", (teacher_username,))
        if not row:
            flash("Professeur introuvable (ou rôle incorrect).", "error")
            return redirect("/admin/")
        teacher_id = row["id"]

    execute(
        "INSERT INTO classes(name, teacher_id) VALUES (%s, %s) ON DUPLICATE KEY UPDATE teacher_id=VALUES(teacher_id)",
        (form.name.data, teacher_id),
    )
    flash("Classe créée/initialisée.", "success")
    return redirect("/admin/")


@admin_bp.route("/classes/<int:class_id>/assign-student", methods=["POST"])
@login_required
@role_required("ADMIN")
def assign_student(class_id: int):
    form = AssignStudentForm()
    if not form.validate_on_submit():
        flash("Nom étudiant invalide.", "error")
        return redirect("/admin/")

    row = fetch_one("SELECT id FROM users WHERE username=%s AND role='STUDENT'", (form.student_username.data,))
    if not row:
        flash("Étudiant introuvable (ou rôle incorrect).", "error")
        return redirect("/admin/")

    execute(
        """
        INSERT INTO class_students(class_id, student_id)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE student_id=student_id
        """,
        (class_id, row["id"]),
    )
    flash("Étudiant assigné.", "success")
    return redirect("/admin/")


@admin_bp.route("/classes/<int:class_id>/schedule/create", methods=["POST"])
@login_required
@role_required("ADMIN")
def create_schedule(class_id: int):
    form = CreateScheduleForm()
    if not form.validate_on_submit():
        flash("Données emploi du temps invalides.", "error")
        return redirect("/admin/")

    execute(
        """
        INSERT INTO schedules(class_id, day_of_week, start_time, end_time, location)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (class_id, form.day_of_week.data, form.start_time.data, form.end_time.data, form.location.data),
    )
    flash("Emploi du temps ajouté.", "success")
    return redirect("/admin/")

