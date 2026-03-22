from flask import Flask, redirect, request, url_for, flash, jsonify
from .config import Config
from .extensions import db, sess


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    sess.init_app(app)

    from .auth import auth_bp
    from .playlists import playlists_bp
    from .staging import staging_bp
    from .liked import liked_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(playlists_bp)
    app.register_blueprint(staging_bp)
    app.register_blueprint(liked_bp)

    with app.app_context():
        from .staging.models import StagedTrack  # noqa: F401
        db.create_all()

    from .services.spotify_client import RateLimitError

    @app.errorhandler(RateLimitError)
    def handle_rate_limit(e):
        # AJAX / JSON callers
        if request.accept_mimetypes.accept_json and \
                not request.accept_mimetypes.accept_html:
            return jsonify({"error": str(e), "rate_limited": True}), 429
        # Regular page requests
        flash(str(e), "warning")
        return redirect(request.referrer or url_for("playlists.index"))

    return app
