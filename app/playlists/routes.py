from flask import render_template, redirect, url_for, session, request, jsonify, Response, flash
from . import playlists_bp
from ..services.spotify_client import get_spotify, get_playlist_tracks, get_playlists, remove_tracks
from ..services.csv_service import export_playlist


def _require_spotify():
    sp = get_spotify()
    if sp is None:
        return None
    return sp


@playlists_bp.route("/")
def index():
    sp = _require_spotify()
    if sp is None:
        return redirect(url_for("auth.login"))
    playlists = get_playlists(sp)
    return render_template("playlists/index.html", playlists=playlists)


@playlists_bp.route("/<playlist_id>")
def detail(playlist_id):
    sp = _require_spotify()
    if sp is None:
        return redirect(url_for("auth.login"))
    playlist_info = sp.playlist(playlist_id, fields="name,id,images")
    tracks = get_playlist_tracks(sp, playlist_id)
    return render_template("playlists/detail.html", playlist=playlist_info, tracks=tracks)


@playlists_bp.route("/<playlist_id>/tracks")
def tracks_json(playlist_id):
    sp = _require_spotify()
    if sp is None:
        return jsonify({"error": "not authenticated"}), 401
    try:
        tracks = get_playlist_tracks(sp, playlist_id)
        return jsonify(tracks)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@playlists_bp.route("/<playlist_id>/remove", methods=["POST"])
def remove(playlist_id):
    sp = _require_spotify()
    if sp is None:
        return jsonify({"error": "not authenticated"}), 401
    data = request.get_json()
    uris = [u for u in data.get("uris", []) if u and u.startswith("spotify:track:")]
    if not uris:
        return jsonify({"error": "no valid uris provided"}), 400
    remove_tracks(sp, playlist_id, uris)
    return jsonify({"removed": len(uris)})


@playlists_bp.route("/<playlist_id>/export")
def export(playlist_id):
    sp = _require_spotify()
    if sp is None:
        return redirect(url_for("auth.login"))
    playlist_info = sp.playlist(playlist_id, fields="name")
    tracks = get_playlist_tracks(sp, playlist_id)
    csv_data = export_playlist(tracks)
    safe_name = playlist_info["name"].replace("/", "-").replace("\\", "-")
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.csv"'},
    )
