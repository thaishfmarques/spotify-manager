# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
./run.sh
```

This creates the venv, installs dependencies, validates `.env`, and starts Flask at `http://127.0.0.1:5000`.

To run manually (after activating venv):

```bash
source venv/bin/activate
python run.py
```

## Environment setup

Copy `.env.example` to `.env` and fill in:

```
SPOTIPY_CLIENT_ID=...
SPOTIPY_CLIENT_SECRET=...
SPOTIPY_REDIRECT_URI=http://127.0.0.1:5000/callback
SECRET_KEY=...
```

The Spotify app on the Developer Dashboard must have `http://127.0.0.1:5000/callback` as a redirect URI.

## Architecture

Flask app using the application factory pattern (`app/__init__.py`). Four blueprints, each in its own subdirectory with `__init__.py` and `routes.py`:

- `auth` — OAuth login/callback/logout via spotipy's `SpotifyOAuth`
- `playlists` — list, view tracks, remove tracks, export CSV
- `liked` — view and export liked tracks
- `staging` — bulk add flow: parse text → search Spotify → review → apply to playlist

### Key design decisions

**`services/spotify_client.py`** is the single layer for all Spotify API calls. It handles:
- **Rate limiting** via `_retry()`: 20-second budget per call; raises `RateLimitError` if `Retry-After` exceeds budget. The app's global error handler in `__init__.py` catches `RateLimitError` and shows a flash message instead of a 500.
- **Proactive pacing**: 100ms minimum gap between calls (`_MIN_CALL_GAP`).
- **In-memory TTL cache**: playlists (5m), playlist tracks (2m), liked tracks (5m), search results (1h). Cache is invalidated after mutations.
- **Token storage**: `FlaskSessionCacheHandler` stores the Spotify OAuth token inside the server-side Flask session (not a file).

**Staging model** (`staging/models.py`): `StagedTrack` rows in SQLite (`instance/staging.db`). Status values: `pending`, `resolved`, `not_found`. The apply route adds all `resolved` tracks to Spotify and deletes them from the table.

**Sessions**: server-side filesystem sessions stored in `flask_session/` (configured via Flask-Session). SQLite database for staging is in `instance/`.

**`services/text_parser.py`**: parses free-form text into `{name, artist}` dicts. Supported formats: `Artist - Song`, `Song by Artist`, or plain `Song`.

**`services/csv_service.py`**: generates CSV downloads for playlists and liked tracks.

### Adding a new blueprint

1. Create `app/<name>/` with `__init__.py` (defines the blueprint) and `routes.py`
2. Register it in `app/__init__.py` with `app.register_blueprint(...)`
3. Add templates under `app/templates/<name>/`
