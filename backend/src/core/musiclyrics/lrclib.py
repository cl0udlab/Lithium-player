from typing import Optional
from .base import (
    DURATION_TOLERANCE,
    Lyrics,
    LyricsProvider,
    LyricsQuery,
    LyricsServiceError,
    lyrics_from_lrc,
    request_json,
    strip_version,
)

LRCLIB_URL = "https://lrclib.net/api"


def _pick(results: list, duration: Optional[float]) -> Optional[str]:
    candidates = [r for r in results or [] if r.get("syncedLyrics")]
    if duration:
        candidates = [
            r
            for r in candidates
            if r.get("duration") and abs(r["duration"] - duration) <= DURATION_TOLERANCE
        ]
        candidates.sort(key=lambda r: abs(r["duration"] - duration))
    return candidates[0]["syncedLyrics"] if candidates else None


class LrclibProvider(LyricsProvider):
    name = "lrclib"

    def search(self, query: LyricsQuery, retries: int) -> Optional[Lyrics]:
        title, artist, duration = query.title, query.artist, query.duration
        steps = []
        if artist:
            params = {"track_name": title, "artist_name": artist}
            if query.album:
                params["album_name"] = query.album
            if duration:
                params["duration"] = int(duration)
            steps.append(("/get", params))
            steps.append(("/search", {"track_name": title, "artist_name": artist}))
        for q in dict.fromkeys([title, strip_version(title)]):
            steps.append(("/search", {"q": q}))

        last_error = None
        for path, params in steps:
            try:
                result = request_json(
                    "GET", f"{LRCLIB_URL}{path}", retries, self.name, params=params
                )
            except LyricsServiceError as e:
                last_error = e
                continue
            if path == "/get":
                lyrics = (result or {}).get("syncedLyrics")
                if lyrics and duration and result.get("duration"):
                    if abs(result["duration"] - duration) > DURATION_TOLERANCE:
                        lyrics = None
            else:
                lyrics = _pick(result, duration)
            if lyrics:
                return lyrics_from_lrc(self.name, lyrics)
        if last_error:
            raise last_error
        return None
