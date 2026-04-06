from flask import Blueprint, flash, redirect, render_template, session, url_for

from app.db import fetch_one
from app.decorators import login_required
from app.forms import LoginForm
from werkzeug.security import check_password_hash


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    # Si déjà connecté
    if session.get("user_id"):
        return redirect(url_for("main.index"))

    form = LoginForm()

    if not form.validate_on_submit():
        return render_template("login.html", form=form)

    # Protection bruteforce
    if session.get("login_attempts", 0) > 5:
        flash("Trop de tentatives. Réessayez plus tard.", "error")
        return render_template("login.html", form=form), 429

    username = form.username.data.strip().lower()

    user = fetch_one(
        "SELECT id, username, password_hash, role, is_banned FROM users WHERE username=%s",
        (username,),
    )

    # Utilisateur introuvable
    if not user:
        return _fail_login(form)

    # Compte banni
    if user.get("is_banned"):
        flash("Compte désactivé.", "error")
        return render_template("login.html", form=form), 403

    stored_hash = user["password_hash"]

    if not check_password_hash(stored_hash, form.password.data):
        return _fail_login(form)

    # Connexion réussie
    session.clear()
    session.update({
        "user_id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "login_attempts": 0
    })
    session.permanent = True

    flash("Connexion réussie 🚀", "success")
    return redirect(url_for("main.index"))


def _fail_login(form):
    session["login_attempts"] = session.get("login_attempts", 0) + 1
    flash("Identifiants invalides.", "error")
    return render_template("login.html", form=form), 401


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("Déconnecté.", "success")
    return redirect(url_for("auth.login"))