"""
Edward Spotify Integration
Level 1 (always works): Windows media keys — play/pause/next/prev with no setup.
Level 2 (optional):     spotipy — current track info and search-to-play.
                        Requires free Spotify Developer credentials in .env.
"""

import ctypes
import os
from typing import Optional

from logger import get_logger

logger = get_logger(__name__)

# Windows virtual key codes for media control
_VK_PLAY_PAUSE = 0xB3
_VK_NEXT_TRACK = 0xB0
_VK_PREV_TRACK = 0xB1
_VK_STOP       = 0xB2


def _media_key(vk: int):
    ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
    ctypes.windll.user32.keybd_event(vk, 0, 2, 0)


def play_pause() -> str:
    _media_key(_VK_PLAY_PAUSE)
    return "Play / Pause toggled ⚡"


def next_track() -> str:
    _media_key(_VK_NEXT_TRACK)
    return "Skipped to next track ⚡"


def prev_track() -> str:
    _media_key(_VK_PREV_TRACK)
    return "Rewound to previous track ⚡"


def stop_media() -> str:
    _media_key(_VK_STOP)
    return "Media stopped ⚡"


# ── Optional spotipy client ───────────────────────────────────────────────────

class SpotifyClient:
    """
    Thin wrapper around spotipy.  Degrades gracefully when credentials
    or the spotipy package are not available — media keys still work.
    """

    SCOPES = (
        "user-read-currently-playing "
        "user-read-playback-state "
        "user-modify-playback-state"
    )

    def __init__(self):
        self._sp   = None
        self._ready = False
        self._init()

    def _init(self):
        client_id     = os.getenv("SPOTIPY_CLIENT_ID", "").strip()
        client_secret = os.getenv("SPOTIPY_CLIENT_SECRET", "").strip()
        redirect_uri  = os.getenv("SPOTIPY_REDIRECT_URI", "http://localhost:8888/callback")

        if not (client_id and client_secret):
            logger.info("Spotify: no API credentials — media key control only")
            return

        try:
            import spotipy
            from spotipy.oauth2 import SpotifyOAuth

            self._sp = spotipy.Spotify(
                auth_manager=SpotifyOAuth(
                    client_id=client_id,
                    client_secret=client_secret,
                    redirect_uri=redirect_uri,
                    scope=self.SCOPES,
                    open_browser=True,
                    cache_path=".spotify_cache",
                )
            )
            # Quick test
            self._sp.current_user()
            self._ready = True
            logger.info("Spotify: spotipy client ready")

        except ImportError:
            logger.info("Spotify: spotipy not installed (pip install spotipy)")
        except Exception as e:
            logger.warning(f"Spotify: spotipy init failed — {e}")

    @property
    def ready(self) -> bool:
        return self._ready

    # ── Info ──────────────────────────────────────────────────────────────────

    def current_track_info(self) -> Optional[str]:
        if not self._ready:
            return None
        try:
            result = self._sp.current_user_playing_track()
            if result and result.get("is_playing"):
                item    = result.get("item", {})
                name    = item.get("name", "Unknown")
                artists = ", ".join(a["name"] for a in item.get("artists", []))
                album   = item.get("album", {}).get("name", "")
                prog_ms = result.get("progress_ms", 0)
                dur_ms  = item.get("duration_ms", 1)
                pct     = int(prog_ms / dur_ms * 100)
                return f"{name} — {artists} ({album}) [{pct}%]"
            elif result:
                return "Spotify is paused."
            return "Nothing playing on Spotify."
        except Exception as e:
            logger.error(f"Spotify current_track: {e}")
            return None

    # ── Playback ──────────────────────────────────────────────────────────────

    def search_and_play(self, query: str) -> Optional[str]:
        if not self._ready:
            return None
        try:
            results = self._sp.search(q=query, limit=1, type="track")
            tracks  = results.get("tracks", {}).get("items", [])
            if not tracks:
                return f"No Spotify results for: {query}"
            track  = tracks[0]
            name   = track["name"]
            artist = track["artists"][0]["name"]
            self._sp.start_playback(uris=[track["uri"]])
            return f"Now playing \"{name}\" by {artist} on Spotify ⚡"
        except Exception as e:
            return f"Spotify search failed: {e}"

    def set_volume(self, pct: int) -> Optional[str]:
        if not self._ready:
            return None
        try:
            pct = max(0, min(100, pct))
            self._sp.volume(pct)
            return f"Spotify volume set to {pct}% ⚡"
        except Exception as e:
            return f"Spotify volume error: {e}"


# ── Singleton ─────────────────────────────────────────────────────────────────

_client: Optional[SpotifyClient] = None


def get_spotify_client() -> SpotifyClient:
    global _client
    if _client is None:
        _client = SpotifyClient()
    return _client
