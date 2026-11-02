import base64
import random
import time
from typing import Optional
from core.logger import logger
from .base import (
    DURATION_TOLERANCE,
    Lyrics,
    LyricsProvider,
    LyricsQuery,
    artist_matches,
    attach_by_time,
    lyrics_from_lrc,
    parse_lrc,
    request_json,
    title_matches,
)
from .qrc import decrypt_qrc, is_qrc, parse_qrc

QQ_URL = "https://u.y.qq.com/cgi-bin/musicu.fcg"
QQ_HEADERS = {
    "Content-Type": "application/json",
    "Cookie": "tmeLoginType=-1;",
    "User-Agent": "okhttp/3.14.9",
}

QQ_COMM = {
    "ct": 11,
    "cv": "1003006",
    "v": "1003006",
    "os_ver": "15",
    "phonetype": "24122RKC7C",
    "rom": "Redmi/miro/miro:15/AE3A.240806.005/OS2.0.102.0.VOMCNXM:user/release-keys",
    "tmeAppID": "qqmusiclight",
    "nettype": "NETWORK_WIFI",
    "udid": "0",
    "uid": "0",
}
INSTRUMENTAL = "纯音乐，请您欣赏"
MAX_CANDIDATES = 3
REFUSED_RETRIES = 3


def _b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


def _decode(text: Optional[str]) -> str:
    if not text:
        return ""
    try:
        return base64.b64decode(text).decode("utf-8", errors="replace")
    except ValueError:
        return ""


class QQMusicProvider(LyricsProvider):
    name = "qqmusic"

    def _request(self, method: str, module: str, param: dict, retries: int):
        payload = {
            "comm": QQ_COMM,
            "request": {"method": method, "module": module, "param": param},
        }
        for attempt in range(REFUSED_RETRIES):
            if attempt:
                time.sleep(attempt)
            data = request_json(
                "POST", QQ_URL, retries, self.name, json=payload, headers=QQ_HEADERS
            )
            code = (
                (data or {}).get("code"),
                ((data or {}).get("request") or {}).get("code"),
            )
            if code == (0, 0):
                return data["request"].get("data")

            if code[1] != 2001:
                break
        logger.debug(f"qqmusic {method} code {code}")
        return None

    def _search(self, query: LyricsQuery, retries: int) -> list[dict]:
        keyword = " ".join(filter(None, [query.title, query.artist]))[:60]
        param = {
            "search_id": str(
                random.randrange(10**14) + int(time.time() * 1000) % 86400000
            ),
            "remoteplace": "search.android.keyboard",
            "query": keyword,
            "search_type": 7,
            "num_per_page": 20,
            "page_num": 1,
            "highlight": 0,
            "nqc_flag": 0,
            "page_id": 1,
            "grp": 1,
        }
        data = self._request(
            "DoSearchForQQMusicLite", "music.search.SearchCgiService", param, retries
        )
        songs = ((data or {}).get("body") or {}).get("item_song") or []

        candidates = []
        for song in songs:
            if not title_matches(query.title, song.get("title") or ""):
                continue
            interval = song.get("interval") or 0
            if query.duration:
                if abs(interval - query.duration) > DURATION_TOLERANCE:
                    continue

            elif not artist_matches(
                query.artist, [s.get("name") or "" for s in song.get("singer") or []]
            ):
                continue
            candidates.append(song)
        if query.duration:
            candidates.sort(
                key=lambda s: abs((s.get("interval") or 0) - query.duration)
            )
        return candidates[:MAX_CANDIDATES]

    def _get_lyric_info(self, song: dict, encrypted: bool, retries: int):
        singers = ", ".join(s.get("name") or "" for s in song.get("singer") or [])

        flag = int(encrypted)
        param = {
            "albumName": _b64((song.get("album") or {}).get("name") or ""),
            "crypt": flag,
            "ct": 19,
            "cv": 2111,
            "interval": song.get("interval") or 0,
            "lrc_t": 0,
            "qrc": flag,
            "qrc_t": 0,
            "roma": flag,
            "roma_t": 0,
            "singerName": _b64(singers),
            "songID": int(song["id"]),
            "songName": _b64(song.get("title") or ""),
            "trans": 1,
            "trans_t": 0,
            "type": 0,
        }
        return self._request(
            "GetPlayLyricInfo", "music.musichallSong.PlayLyricInfo", param, retries
        )

    def _fetch_qrc(self, song: dict, retries: int) -> Optional[Lyrics]:
        data = self._get_lyric_info(song, True, retries) or {}
        if not data.get("lyric"):
            return None
        lyric = decrypt_qrc(data["lyric"])
        trans = decrypt_qrc(data["trans"]) if data.get("trans") else ""
        if INSTRUMENTAL in lyric:
            return None
        if not is_qrc(lyric):
            return lyrics_from_lrc(self.name, lyric, trans)

        lines = parse_qrc(lyric)
        if not lines:
            return None
        attach_by_time(lines, parse_lrc(trans), "translation")
        if data.get("roma"):
            try:
                roma = parse_qrc(decrypt_qrc(data["roma"]))
                attach_by_time(lines, [(r.start, r.text) for r in roma], "romanization")
            except ValueError as e:
                logger.debug(f"qqmusic 羅馬音解密失敗: {str(e)}")
        return Lyrics(source=self.name, lines=lines)

    def _fetch_lrc(self, song: dict, retries: int) -> Optional[Lyrics]:
        data = self._get_lyric_info(song, False, retries) or {}
        lyric = _decode(data.get("lyric"))
        if not lyric or INSTRUMENTAL in lyric:
            return None
        return lyrics_from_lrc(self.name, lyric, _decode(data.get("trans")))

    def _fetch(self, song: dict, retries: int) -> Optional[Lyrics]:
        try:
            return self._fetch_qrc(song, retries)
        except ValueError as e:
            logger.warning(f"qqmusic QRC 解密失敗, 改用逐句 LRC: {str(e)}")
            return self._fetch_lrc(song, retries)

    def search(self, query: LyricsQuery, retries: int) -> Optional[Lyrics]:
        for song in self._search(query, retries):
            lyrics = self._fetch(song, retries)
            if lyrics:
                return lyrics
        return None
