from functools import wraps

import logging

from flask import abort, g, redirect, request, session, url_for


logger = logging.getLogger(__name__)


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user_id = session.get("user_id")
        role = session.get("role")
        if not user_id or not role:
            logger.warning(
                "Unauthorized access (not logged in). path=%s remote=%s",
                request.path,
                request.remote_addr,
            )
            return redirect(url_for("auth.login"))
        g.current_user = {"user_id": user_id, "role": role, "username": session.get("username")}
        return view_func(*args, **kwargs)

    return wrapper


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            role = session.get("role")
            if role not in allowed_roles:
                logger.warning(
                    "Unauthorized access (role denied). role=%s path=%s remote=%s",
                    role,
                    request.path,
                    request.remote_addr,
                )
                abort(403)
            return view_func(*args, **kwargs)

        return wrapper

    return decorator

