from flask import redirect, request, session, url_for, flash
from . import auth_bp
from ..services.spotify_client import get_auth_url, get_token_from_code


@auth_bp.route("/")
def index():
    if session.get("token_info"):
        return redirect(url_for("playlists.index"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/login")
def login():
    auth_url = get_auth_url()
    return redirect(auth_url)


@auth_bp.route("/callback")
def callback():
    error = request.args.get("error")
    if error:
        flash(f"Spotify authorization failed: {error}", "danger")
        return redirect(url_for("auth.login"))

    code = request.args.get("code")
    if not code:
        flash("No authorization code received.", "danger")
        return redirect(url_for("auth.login"))

    token_info = get_token_from_code(code)
    session["token_info"] = token_info
    return redirect(url_for("playlists.index"))


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
