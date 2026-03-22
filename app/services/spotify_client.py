import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import CacheHandler
from flask import session as flask_session
from flask import current_app


SCOPES = (
    "playlist-read-private "
    "playlist-read-collaborative "
    "playlist-modify-public "
    "playlist-modify-private "
    "user-library-read"
)

# ---------------------------------------------------------------------------
# Rate limit error
# ---------------------------------------------------------------------------

class RateLimitError(Exception):
    """Raised when Spotify keeps rate-limiting us past the request budget."""
    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(
            f"Limite de requisições do Spotify atingido. "
            f"Aguarde {retry_after} segundo(s) e tente novamente."
        )


# ---------------------------------------------------------------------------
# In-memory TTL cache  {key: (expires_at, value)}
# ---------------------------------------------------------------------------

_cache: dict = {}
_MIN_CALL_GAP = 0.1   # min seconds between any API call (proactive pacing)
_last_call_ts: float = 0.0


def _cache_get(key: str):
    entry = _cache.get(key)
    if entry and time.time() < entry[0]:
        return entry[1]
    _cache.pop(key, None)
    return None


def _cache_set(key: str, value, ttl: int):
    _cache[key] = (time.time() + ttl, value)


def _cache_delete_prefix(prefix: str):
    for k in list(_cache):
        if k.startswith(prefix):
            del _cache[k]


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

class FlaskSessionCacheHandler(CacheHandler):
    """Stores the Spotify token inside the Flask server-side session."""

    def get_cached_token(self):
        return flask_session.get("token_info")

    def save_token_to_cache(self, token_info):
        flask_session["token_info"] = token_info
        flask_session.modified = True


def _make_oauth():
    return SpotifyOAuth(
        client_id=current_app.config["SPOTIPY_CLIENT_ID"],
        client_secret=current_app.config["SPOTIPY_CLIENT_SECRET"],
        redirect_uri=current_app.config["SPOTIPY_REDIRECT_URI"],
        scope=SCOPES,
        cache_handler=FlaskSessionCacheHandler(),
        show_dialog=False,
    )


def get_auth_url():
    return _make_oauth().get_authorize_url()


def get_token_from_code(code):
    oauth = _make_oauth()
    return oauth.get_access_token(code)


def get_spotify():
    oauth = _make_oauth()
    token_info = oauth.validate_token(flask_session.get("token_info"))
    if not token_info:
        return None
    # retries=0: disable spotipy's built-in urllib3 Retry adapter so it doesn't
    # sleep for Retry-After seconds internally. Our _retry() handles all retrying.
    return spotipy.Spotify(auth=token_info["access_token"], retries=0)


# ---------------------------------------------------------------------------
# Retry with budget (avoids indefinite blocking)
# ---------------------------------------------------------------------------

def _retry(fn, *args, budget_secs: int = 20, **kwargs):
    """Call fn(*args, **kwargs) retrying on 429/5xx within a time budget.

    Raises RateLimitError if Spotify keeps rate-limiting past the budget.
    """
    global _last_call_ts

    # Proactive pacing: enforce minimum gap between API calls
    gap = _MIN_CALL_GAP - (time.time() - _last_call_ts)
    if gap > 0:
        time.sleep(gap)

    deadline = time.time() + budget_secs
    backoff = 1

    while True:
        try:
            result = fn(*args, **kwargs)
            _last_call_ts = time.time()
            return result
        except spotipy.SpotifyException as e:
            if e.http_status == 429:
                wait = int(e.headers.get("Retry-After", 2)) if e.headers else 2
                if time.time() + wait > deadline:
                    raise RateLimitError(wait) from e
                time.sleep(wait)
            elif e.http_status and e.http_status >= 500:
                if time.time() + backoff > deadline:
                    raise
                time.sleep(backoff)
                backoff = min(backoff * 2, 10)
            else:
                raise


# ---------------------------------------------------------------------------
# Spotify API wrappers
# ---------------------------------------------------------------------------

def get_playlists(sp):
    cached = _cache_get("playlists")
    if cached is not None:
        return cached

    results = []
    response = _retry(sp.current_user_playlists, limit=50)
    while response:
        for item in response["items"]:
            if item and item.get("tracks") is None:
                details = _retry(sp.playlist, item["id"], fields="tracks.total")
                item["tracks"] = details.get("tracks") or {"total": 0}
            results.append(item)
        response = _retry(sp.next, response) if response["next"] else None

    _cache_set("playlists", results, ttl=300)
    return results


def get_playlist_tracks(sp, playlist_id):
    key = f"playlist_tracks:{playlist_id}"
    cached = _cache_get(key)
    if cached is not None:
        return cached

    tracks = []
    response = _retry(sp.playlist_tracks, playlist_id, limit=100)
    while response:
        for item in response["items"]:
            track = item.get("track") or item.get("item")
            if not track or not track.get("uri"):
                continue
            tracks.append({
                "name": track.get("name", ""),
                "artist": ", ".join(a["name"] for a in track.get("artists", [])),
                "album": (track.get("album") or {}).get("name", ""),
                "duration_ms": track.get("duration_ms", 0),
                "uri": track["uri"],
            })
        response = _retry(sp.next, response) if response["next"] else None

    _cache_set(key, tracks, ttl=120)
    return tracks


def get_liked_tracks(sp):
    cached = _cache_get("liked_tracks")
    if cached is not None:
        return cached

    tracks = []
    response = _retry(sp.current_user_saved_tracks, limit=50)
    while response:
        for item in response["items"]:
            track = item.get("track")
            if not track or not track.get("uri"):
                continue
            tracks.append({
                "name": track.get("name", ""),
                "artist": ", ".join(a["name"] for a in track.get("artists", [])),
                "album": (track.get("album") or {}).get("name", ""),
                "duration_ms": track.get("duration_ms", 0),
                "uri": track["uri"],
                "added_at": item.get("added_at", ""),
            })
        response = _retry(sp.next, response) if response["next"] else None

    _cache_set("liked_tracks", tracks, ttl=300)
    return tracks


def search_track(sp, name, artist=""):
    cache_key = f"search:{name.lower()}:{artist.lower()}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    query = f"track:{name}"
    if artist:
        query += f" artist:{artist}"
    results = _retry(sp.search, query, limit=1, type="track")
    items = results["tracks"]["items"]
    if items:
        uri = items[0]["uri"]
        _cache_set(cache_key, uri, ttl=3600)
        return uri

    # Fallback: plain text search
    fallback = f"{name} {artist}".strip()
    results = _retry(sp.search, fallback, limit=1, type="track")
    items = results["tracks"]["items"]
    uri = items[0]["uri"] if items else None
    if uri:
        _cache_set(cache_key, uri, ttl=3600)
    return uri


def remove_tracks(sp, playlist_id, uris):
    for i in range(0, len(uris), 100):
        batch = uris[i:i + 100]
        _retry(sp.playlist_remove_all_occurrences_of_items, playlist_id, batch)
    _cache_delete_prefix(f"playlist_tracks:{playlist_id}")


def add_tracks(sp, playlist_id, uris):
    for i in range(0, len(uris), 100):
        batch = uris[i:i + 100]
        _retry(sp.playlist_add_items, playlist_id, batch)
    _cache_delete_prefix(f"playlist_tracks:{playlist_id}")
