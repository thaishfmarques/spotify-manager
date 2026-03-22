from flask import render_template, redirect, url_for, request, flash, jsonify
from . import staging_bp
from .models import StagedTrack
from ..extensions import db
from ..services.spotify_client import get_spotify, get_playlists, search_track, add_tracks, RateLimitError
from ..services.text_parser import parse


def _require_spotify():
    sp = get_spotify()
    if sp is None:
        return None
    return sp


@staging_bp.route("/")
def index():
    sp = _require_spotify()
    if sp is None:
        return redirect(url_for("auth.login"))
    playlists = get_playlists(sp)
    staged = StagedTrack.query.order_by(StagedTrack.created_at.desc()).all()
    return render_template("staging/index.html", staged=staged, playlists=playlists)


@staging_bp.route("/upload", methods=["POST"])
def upload():
    sp = _require_spotify()
    if sp is None:
        return redirect(url_for("auth.login"))

    playlist_id = request.form.get("playlist_id", "").strip()
    playlist_name = request.form.get("playlist_name", "").strip()

    # Get text from textarea or file upload
    text = ""
    file = request.files.get("file")
    if file and file.filename:
        text = file.read().decode("utf-8", errors="replace")
    else:
        text = request.form.get("text", "")

    if not playlist_id:
        flash("Please select a target playlist.", "warning")
        return redirect(url_for("staging.index"))
    if not text.strip():
        flash("No tracks provided.", "warning")
        return redirect(url_for("staging.index"))

    entries = parse(text)
    resolved = 0
    not_found = 0
    rate_limited = 0

    for entry in entries:
        try:
            uri = search_track(sp, entry["name"], entry["artist"])
            status = "resolved" if uri else "not_found"
            if uri:
                resolved += 1
            else:
                not_found += 1
        except RateLimitError:
            uri = None
            status = "pending"
            rate_limited += 1
        track = StagedTrack(
            playlist_id=playlist_id,
            playlist_name=playlist_name,
            name=entry["name"],
            artist=entry["artist"],
            uri=uri,
            status=status,
        )
        db.session.add(track)

    db.session.commit()
    msg = f"{resolved} resolvidas, {not_found} não encontradas."
    if rate_limited:
        msg += (
            f" {rate_limited} salvas como 'pendente' — limite de requisições atingido. "
            "Use o botão Retry para tentar novamente."
        )
        flash(msg, "warning")
    else:
        flash(msg, "info")
    return redirect(url_for("staging.index"))


@staging_bp.route("/retry-pending", methods=["POST"])
def retry_pending():
    sp = _require_spotify()
    if sp is None:
        return redirect(url_for("auth.login"))

    playlist_id = request.form.get("playlist_id", "").strip()
    query = StagedTrack.query.filter_by(status="pending")
    if playlist_id:
        query = query.filter_by(playlist_id=playlist_id)

    pending = query.all()
    if not pending:
        flash("Nenhuma faixa pendente.", "info")
        return redirect(url_for("staging.index"))

    resolved = rate_limited = 0
    for track in pending:
        try:
            uri = search_track(sp, track.name, track.artist)
            track.uri = uri
            track.status = "resolved" if uri else "not_found"
            if uri:
                resolved += 1
        except RateLimitError:
            rate_limited += 1
            break  # stop and let user retry again later

    db.session.commit()
    msg = f"{resolved} resolvidas."
    if rate_limited:
        msg += f" {rate_limited} ainda pendentes — limite atingido novamente. Tente em instantes."
        flash(msg, "warning")
    else:
        flash(msg, "success")
    return redirect(url_for("staging.index"))


@staging_bp.route("/remove/<int:track_id>", methods=["POST"])
def remove(track_id):
    track = StagedTrack.query.get_or_404(track_id)
    db.session.delete(track)
    db.session.commit()
    return redirect(url_for("staging.index"))


@staging_bp.route("/set-uri/<int:track_id>", methods=["POST"])
def set_uri(track_id):
    track = StagedTrack.query.get_or_404(track_id)
    uri = request.form.get("uri", "").strip()
    if uri:
        track.uri = uri
        track.status = "resolved"
        db.session.commit()
        flash("URI updated.", "success")
    return redirect(url_for("staging.index"))


@staging_bp.route("/apply", methods=["POST"])
def apply():
    sp = _require_spotify()
    if sp is None:
        return redirect(url_for("auth.login"))

    playlist_id = request.form.get("playlist_id", "").strip()
    query = StagedTrack.query.filter_by(status="resolved")
    if playlist_id:
        query = query.filter_by(playlist_id=playlist_id)

    tracks = query.all()
    if not tracks:
        flash("No resolved tracks to apply.", "warning")
        return redirect(url_for("staging.index"))

    uris = [t.uri for t in tracks]
    add_tracks(sp, playlist_id or tracks[0].playlist_id, uris)

    for t in tracks:
        db.session.delete(t)
    db.session.commit()

    flash(f"Added {len(uris)} tracks to the playlist.", "success")
    return redirect(url_for("staging.index"))


@staging_bp.route("/clear", methods=["POST"])
def clear():
    playlist_id = request.form.get("playlist_id", "").strip()
    query = StagedTrack.query
    if playlist_id:
        query = query.filter_by(playlist_id=playlist_id)
    count = query.count()
    query.delete()
    db.session.commit()
    flash(f"Cleared {count} staged tracks.", "info")
    return redirect(url_for("staging.index"))
