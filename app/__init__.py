import logging

from flask import Flask, redirect, render_template
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
from dotenv import load_dotenv

from .config import Config
from .security import security_headers

csrf = CSRFProtect()
logger = logging.getLogger(__name__)


def create_app():
    load_dotenv(override=False)
    app = Flask(__name__, template_folder="templates")
    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["WTF_CSRF_ENABLED"] = Config.CSRF_ENABLED
    app.config["SESSION_COOKIE_HTTPONLY"] = Config.SESSION_COOKIE_HTTPONLY
    app.config["SESSION_COOKIE_SAMESITE"] = Config.SESSION_COOKIE_SAMESITE
    app.config["SESSION_COOKIE_SECURE"] = Config.SESSION_COOKIE_SECURE
    app.config["PERMANENT_SESSION_LIFETIME"] = Config.PERMANENT_SESSION_LIFETIME_SECONDS
    app.config["SURPRISE_IMAGE_URL"] = Config.SURPRISE_IMAGE_URL
    app.config["DASHBOARD_BG_PATH"] = Config.DASHBOARD_BG_PATH

    csrf.init_app(app)

    from .routes.auth import auth_bp
    from .routes.main import main_bp
    from .routes.admin import admin_bp
    from .routes.teacher import teacher_bp
    from .routes.student import student_bp
    from .routes.schedule import schedule_bp
    # from .routes.love import love_bp
    # from .routes.blackjack import blackjack_bp



    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(schedule_bp)
    # app.register_blueprint(love_bp)
    # app.register_blueprint(blackjack_bp)

    @app.after_request
    def apply_security_headers(response):
        headers = security_headers()
        for k, v in headers.items():
            if v is not None:
                response.headers[k] = v
        return response

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("unauthorized.html"), 403

    @app.errorhandler(CSRFError)
    def csrf_invalid(_e):
        return render_template("unauthorized.html"), 403

    @app.errorhandler(404)
    def not_found(_e):
        return redirect("/")

    return app

