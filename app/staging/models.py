from datetime import datetime
from ..extensions import db


class StagedTrack(db.Model):
    __tablename__ = "staged_tracks"

    id = db.Column(db.Integer, primary_key=True)
    playlist_id = db.Column(db.String(64), nullable=False)
    playlist_name = db.Column(db.String(256), nullable=False, default="")
    name = db.Column(db.String(256), nullable=False)
    artist = db.Column(db.String(256), nullable=False, default="")
    uri = db.Column(db.String(128), nullable=True)
    status = db.Column(db.String(16), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
