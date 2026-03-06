from functools import wraps

from flask import Blueprint, abort, redirect, request, url_for
from flask_login import current_user


admin_bp = Blueprint('admin', __name__)


def admin_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login', next=request.url))
        if current_user.role != 'admin':
            abort(403)
        return func(*args, **kwargs)

    return decorated_function


from . import routes  # noqa: E402,F401
