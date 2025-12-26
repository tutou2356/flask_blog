from flask import Blueprint


blog_bp = Blueprint('blog', __name__)

from . import routes  # noqa: E402,F401
