from flask import render_template, redirect, url_for, Response
from . import liked_bp
from ..services.spotify_client import get_spotify, get_liked_tracks
from ..services.csv_service import export_playlist


def _require_spotify():
    sp = get_spotify()
    if sp is None:
        return None
    return sp


@liked_bp.route("/")
def index():
    sp = _require_spotify()
    if sp is None:
        return redirect(url_for("auth.login"))
    tracks = get_liked_tracks(sp)
    return render_template("liked/index.html", tracks=tracks)


@liked_bp.route("/export")
def export():
    sp = _require_spotify()
    if sp is None:
        return redirect(url_for("auth.login"))
    tracks = get_liked_tracks(sp)
    csv_data = export_playlist(tracks)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": 'attachment; filename="curtidas.csv"'},
    )
