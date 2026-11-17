"""Subsonic client and durable, atomically published audio cache."""
import hashlib
import secrets
import threading
import time
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

import httpx
from pydantic import BaseModel, field_validator

DATA = Path("data/subsonic")
_lock = threading.RLock()


class SubsonicError(Exception):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


class Connection(BaseModel):
    url: str
    username: str
    password: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, value):
        value = value.strip().rstrip("/")
        if value.endswith("/rest"):
            value = value[:-5]
        parsed = urlsplit(value)
        if (parsed.scheme not in ("http", "https") or not parsed.hostname
                or parsed.username or parsed.password or parsed.query or parsed.fragment):
            raise ValueError("請輸入有效的 HTTP(S) 伺服器網址，不包含帳密或查詢參數")
        return value

    @field_validator("username")
    @classmethod
    def validate_username(cls, value):
        if not value.strip():
            raise ValueError("使用者名稱不可為空")
        return value.strip()

    @property
    def identity(self):
        return hashlib.sha256(f"{self.url}\n{self.username}".encode()).hexdigest()


def load_connection():
    with _lock:
        path = DATA / "connection.json"
        return Connection.model_validate_json(path.read_text(encoding="utf-8")) if path.exists() else None


def save_connection(connection):
    with _lock:
        DATA.mkdir(parents=True, exist_ok=True)
        temporary = DATA / "connection.tmp"
        temporary.write_text(connection.model_dump_json(), encoding="utf-8")
        temporary.replace(DATA / "connection.json")


def disconnect():
    with _lock:
        (DATA / "connection.json").unlink(missing_ok=True)


def params(connection, **extra):
    salt = secrets.token_hex(12)
    return {"u": connection.username, "t": hashlib.md5(
        (connection.password + salt).encode("utf-8")).hexdigest(),
        "s": salt, "v": "1.16.1", "c": "LithiumPlayer", "f": "json", **extra}


def call(connection, method, **extra):
    try:
        response = httpx.get(f"{connection.url}/rest/{method}.view",
                             params=params(connection, **extra), timeout=20, follow_redirects=True)
        response.raise_for_status()
        body = response.json()["subsonic-response"]
        if body.get("status") != "ok":
            code = body.get("error", {}).get("code", 0)
            raise SubsonicError(f"Subsonic API 錯誤（代碼 {code}）", code=code)
        return body
    except httpx.HTTPStatusError as exc:
        raise SubsonicError("Subsonic API 暫時無法使用", code=0 if exc.response.status_code == 404 else None) from exc
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        raise SubsonicError("無法連線至 Subsonic 伺服器，請檢查網址與連線") from exc


def library(connection):
    """Stage a complete paged snapshot before touching the existing library."""
    songs = {}
    offset = 0
    seen_pages = set()
    while True:
        albums = call(connection, "getAlbumList2", type="alphabeticalByName",
                      size=500, offset=offset).get("albumList2", {}).get("album", [])
        if not albums:
            break
        page = tuple(str(album["id"]) for album in albums)
        if page in seen_pages:
            raise SubsonicError("伺服器未正確支援分頁，同步已取消，原有曲目已保留")
        seen_pages.add(page)
        for album in albums:
            detail = call(connection, "getAlbum", id=album["id"]).get("album", {})
            for song in detail.get("song", []):
                songs[str(song["id"])] = {"albumId": album["id"], "album": detail.get("name", album.get("name")),
                    "albumArtist": detail.get("artist", album.get("artist")),
                    "coverArt": detail.get("coverArt", album.get("coverArt")), **song}
        offset += len(albums)
    return list(songs.values())


def song_url(connection, song_id):
    return f"subsonic://{connection.identity}/{quote(str(song_id), safe='')}"


def connection_for(url):
    connection = load_connection()
    parsed = urlsplit(url)
    if not connection or parsed.netloc != connection.identity:
        raise SubsonicError("此曲目的來源已中斷連結；已快取的歌曲仍可播放")
    return connection, unquote(parsed.path[1:])


def cache_path(url):
    return DATA / "audio" / (hashlib.sha256(url.encode()).hexdigest() + ".audio")


def cached_audio(url):
    """Download fully before publishing, so interrupted downloads never become playable cache."""
    path = cache_path(url)
    if path.exists():
        return path
    with _lock:
        if path.exists():
            return path
        connection, song_id = connection_for(url)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".part")
        try:
            with httpx.stream("GET", f"{connection.url}/rest/download.view",
                              params=params(connection, id=song_id),
                              timeout=httpx.Timeout(20, read=60), follow_redirects=True) as response:
                response.raise_for_status()
                content_type = response.headers.get("content-type", "").lower()
                if any(value in content_type for value in ("json", "xml", "text/")):
                    raise SubsonicError("Subsonic 未回傳音訊，請檢查帳號下載權限")
                count = 0
                with temporary.open("wb") as output:
                    for chunk in response.iter_bytes():
                        output.write(chunk)
                        count += len(chunk)
                expected = response.headers.get("content-length")
                if not count or (expected and count != int(expected)):
                    raise SubsonicError("下載不完整，請恢復連線後重試")
            temporary.replace(path)
            return path
        except (httpx.HTTPError, OSError, ValueError) as exc:
            raise SubsonicError("來源無法連線且歌曲尚未快取，請恢復連線後重試") from exc
        finally:
            temporary.unlink(missing_ok=True)


_cover_guard = threading.Lock()
_cover_locks = {}
_cover_failures = {}
_cover_slots = threading.BoundedSemaphore(3)


def cover(url, art):
    source = urlsplit(url).netloc
    key = hashlib.sha256(f"{source}\n{art}".encode()).hexdigest()
    path = DATA / "covers" / key
    if path.exists():
        return path
    with _cover_guard:
        lock = _cover_locks.setdefault(key, threading.Lock())
    with lock:
        if path.exists():
            return path
        if _cover_failures.get(key, 0) > time.monotonic():
            raise SubsonicError("封面來源暫時無法使用，請稍後重試")
        try:
            connection, _ = connection_for(url)
            with _cover_slots:
                response = httpx.get(f"{connection.url}/rest/getCoverArt.view",
                    params=params(connection, id=art, size=600), timeout=20, follow_redirects=True)
                response.raise_for_status()
            if not response.headers.get("content-type", "").startswith("image/"):
                raise SubsonicError("找不到封面")
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(".tmp")
            temporary.write_bytes(response.content)
            temporary.replace(path)
            return path
        except (httpx.HTTPError, OSError, SubsonicError) as exc:
            _cover_failures[key] = time.monotonic() + 30
            raise SubsonicError("封面來源暫時無法使用，請稍後重試") from exc


def lyrics(url, title, artist):
    connection, song_id = connection_for(url)
    errors = []
    try:
        entries = call(connection, "getLyricsBySongId", id=song_id).get("lyricsList", {}).get("structuredLyrics", [])
        for entry in sorted(entries, key=lambda item: not item.get("synced", False)):
            lines = []
            for line in entry.get("line", []):
                text = line.get("value", "")
                if entry.get("synced") and line.get("start") is not None:
                    seconds = max(0, float(line["start"]) + float(entry.get("offset") or 0)) / 1000
                    text = f"[{int(seconds // 60):02d}:{seconds % 60:05.2f}]{text}"
                lines.append(text)
            if any(line.get("value", "").strip() for line in entry.get("line", [])):
                return "\n".join(lines)
    except SubsonicError as exc:
        if exc.code not in (0, 20, 30, 70):
            errors.append(exc)
    try:
        content = call(connection, "getLyrics", artist=artist, title=title).get("lyrics", {}).get("value")
        if content:
            return content
    except SubsonicError as exc:
        if exc.code not in (0, 20, 30, 70):
            errors.append(exc)
    if errors:
        raise errors[-1]
    return None
