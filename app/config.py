import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")

    if not SECRET_KEY:
        raise ValueError("SECRET_KEY manquant (FLASK_SECRET_KEY)")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"

    PERMANENT_SESSION_LIFETIME_SECONDS = int(
        os.environ.get("SESSION_LIFETIME_SECONDS", "3600")
    )

    MYSQL_HOST = os.environ.get("MYSQL_HOST", "db")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
    MYSQL_USER = os.environ.get("MYSQL_USER", "devsecops")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "devsecops")
    MYSQL_DB = os.environ.get("MYSQL_DB", "devsecops")

    CSRF_ENABLED = True

    DATA_ENCRYPTION_KEY = os.environ.get("DATA_ENCRYPTION_KEY")

    if not DATA_ENCRYPTION_KEY:
        raise ValueError("DATA_ENCRYPTION_KEY manquante")

    SURPRISE_IMAGE_URL = os.environ.get(
        "SURPRISE_IMAGE_URL",
        "/static/images/surprise-face.png"
    )

    DASHBOARD_BG_PATH = os.environ.get(
        "DASHBOARD_BG_PATH",
        r"C:\Users\eguillonvongsouvan\Downloads\unnamed.jpg",
    )