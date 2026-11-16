"""Subsonic client and durable, atomically published audio cache."""
import hashlib
import secrets
import threading
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

import httpx
from pydantic import BaseModel, field_validator

DATA = Path("data/subsonic")
_lock = threading.RLock()


class SubsonicError(Exception):
    pass


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
            raise SubsonicError(f"Subsonic API 錯誤（代碼 {code}）")
        return body
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
            for song in call(connection, "getAlbum", id=album["id"]).get("album", {}).get("song", []):
                songs[str(song["id"])] = song
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


def cover(url, art):
    path = DATA / "covers" / hashlib.sha256(f"{url}\n{art}".encode()).hexdigest()
    if path.exists():
        return path
    connection, _ = connection_for(url)
    try:
        response = httpx.get(f"{connection.url}/rest/getCoverArt.view",
                             params=params(connection, id=art, size=300), timeout=20,
                             follow_redirects=True)
        response.raise_for_status()
        if not response.headers.get("content-type", "").startswith("image/"):
            raise SubsonicError("找不到封面")
        with _lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(".tmp")
            temporary.write_bytes(response.content)
            temporary.replace(path)
        return path
    except httpx.HTTPError as exc:
        raise SubsonicError("無法取得封面") from exc
