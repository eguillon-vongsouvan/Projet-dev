import base64
import logging

import bcrypt
from cryptography.fernet import Fernet, InvalidToken

from .config import Config

logger = logging.getLogger(__name__)


def hash_password(plain: str) -> bytes:
    plain_bytes = plain.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_bytes, salt)


def check_password(plain: str, password_hash: bytes) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), password_hash)


def get_fernet() -> Fernet | None:
    key = Config.DATA_ENCRYPTION_KEY
    if not key:
        return None
    try:
        # Fernet accepte une clé base64 url-safe 32 bytes.
        # On ne fait qu’un aller-retour de validation de format ici.
        base64.urlsafe_b64decode(key.encode("utf-8"))
        return Fernet(key.encode("utf-8"))
    except Exception:
        return None


def encrypt_value(value: str) -> str:
    f = get_fernet()
    if f is None:
        # Mode démo : pas de chiffrement si clé manquante.
        return value
    token = f.encrypt(value.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_value(value: str) -> str:
    f = get_fernet()
    if f is None:
        return value
    try:
        raw = f.decrypt(value.encode("utf-8"))
        return raw.decode("utf-8")
    except InvalidToken:
        # Si clé différente, on renvoie la donnée brute (évite crash).
        return value


def security_headers() -> dict:
    # CSP minimaliste : accepte styles inline pour les templates simples.
    # On autorise l'iframe YouTube en mode "nocookie" uniquement sur la page Accueil.
    csp = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https://i.ytimg.com; "
        "frame-src https://www.youtube-nocookie.com https://www.youtube.com; "
        "object-src 'none'; "
        "base-uri 'self';"
    )
    return {
        "Content-Security-Policy": csp,
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
        # HSTS : active uniquement si HTTPS (voir SESSION_COOKIE_SECURE)
        "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload"
        if Config.SESSION_COOKIE_SECURE
        else None,
    }

