from flask import Blueprint

liked_bp = Blueprint("liked", __name__, url_prefix="/liked")

from . import routes  # noqa: F401, E402
