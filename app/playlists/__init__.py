from flask import Blueprint

playlists_bp = Blueprint("playlists", __name__, url_prefix="/playlists")

from . import routes  # noqa: F401, E402
