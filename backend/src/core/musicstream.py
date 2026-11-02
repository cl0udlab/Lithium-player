import json
import os
import re
import time
import requests
from pydantic import BaseModel
from yt_dlp import YoutubeDL
from core.logger import logger
from typing import Optional
from sqlmodel import Session, select
from models import StreamPlatform, StreamTrack
from core.musiclyrics import find_lyrics, LyricsServiceError


AUDIO_FORMAT = "bestaudio[ext=m4a]/bestaudio/best"

STREAM_URL_TTL = 60 * 60

BASE_OPTS = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "socket_timeout": 15,
}

if os.getenv("YTDLP_COOKIES"):
    BASE_OPTS["cookiefile"] = os.getenv("YTDLP_COOKIES")


def platform_from_extractor(extractor_key: str) -> StreamPlatform:
    extractor_key = (extractor_key or "").lower()
    if "youtube" in extractor_key:
        return StreamPlatform.YOUTUBE
    elif "bilibili" in extractor_key:
        return StreamPlatform.BILIBILI
    elif "soundcloud" in extractor_key:
        return StreamPlatform.SOUNDCLOUD
    return StreamPlatform.UNKNOWN


def detect_url_type(url: str) -> StreamPlatform:
    try:
        with YoutubeDL(BASE_OPTS) as ydl:
            ie_result = ydl.extract_info(url, download=False, process=False)
        if ie_result is None:
            return StreamPlatform.UNKNOWN
        return platform_from_extractor(ie_result.get("extractor_key", ""))
    except Exception:
        return StreamPlatform.UNKNOWN


class StreamInfo(BaseModel):
    url: str
    title: str
    artist: str = "Unknown Artist"
    platform: StreamPlatform = StreamPlatform.UNKNOWN
    thumbnail: Optional[str] = None
    duration: int = 0


class PlayableStream(BaseModel):
    url: str
    headers: dict[str, str] = {}
    expires_at: float

    available_at: float = 0

    chunk_size: Optional[int] = None


def _to_stream_info(info: dict, fallback_url: str) -> StreamInfo:
    thumbnail = info.get("thumbnail") or (
        (info.get("thumbnails") or [{}])[-1].get("url")
    )
    if thumbnail and thumbnail.startswith("http://"):
        thumbnail = "https://" + thumbnail[len("http://") :]
    return StreamInfo(
        url=info.get("webpage_url") or info.get("original_url") or fallback_url,
        title=info.get("title") or fallback_url,
        artist=info.get("uploader")
        or info.get("artist")
        or info.get("channel")
        or "Unknown Artist",
        platform=platform_from_extractor(
            info.get("extractor_key") or info.get("ie_key", "")
        ),
        thumbnail=thumbnail,
        duration=int(info.get("duration") or 0),
    )


def extract_stream_infos(url: str) -> list[StreamInfo]:
    opts = {**BASE_OPTS, "noplaylist": False, "extract_flat": "in_playlist"}
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        raise ValueError("無法取得stream資訊")

    if info.get("_type") == "playlist":
        entries = [e for e in info.get("entries") or [] if e]
        results = []
        for entry in entries:
            entry_url = entry.get("url") or entry.get("webpage_url")
            if not entry_url:
                continue

            entry.setdefault("extractor_key", info.get("extractor_key"))
            if entry.get("ie_key"):
                entry["extractor_key"] = entry["ie_key"]
            results.append(_to_stream_info(entry, entry_url))
        return results

    return [_to_stream_info(info, url)]


_playable_cache: dict[str, PlayableStream] = {}


def get_playable_stream(url: str) -> PlayableStream:
    cached = _playable_cache.get(url)
    if cached and cached.expires_at > time.time():
        return cached

    with YoutubeDL({**BASE_OPTS, "format": AUDIO_FORMAT}) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        raise ValueError("無法取得stream資訊")

    fmt = info
    if not info.get("url") and info.get("requested_formats"):
        fmt = info["requested_formats"][0]
    stream_url = fmt.get("url")
    headers = fmt.get("http_headers") or info.get("http_headers") or {}
    if not stream_url:
        raise ValueError("找不到可播放的音訊")

    playable = PlayableStream(
        url=stream_url,
        headers={k: str(v) for k, v in headers.items()},
        expires_at=time.time() + STREAM_URL_TTL,
        available_at=fmt.get("available_at") or 0,
        chunk_size=(fmt.get("downloader_options") or {}).get("http_chunk_size"),
    )
    _playable_cache[url] = playable
    return playable


def invalidate_playable_stream(url: str):
    _playable_cache.pop(url, None)


SUBTITLE_LANGS = [
    "zh-Hant",
    "zh-TW",
    "zh-HK",
    "zh",
    "zh-Hans",
    "zh-CN",
    "ja",
    "ko",
    "en",
]
SKIP_SUBTITLES = {"live_chat", "danmaku"}
SUBTITLE_EXTS = ("json3", "vtt", "srt")


def _lang_rank(lang: str) -> int:
    base = lang.removesuffix("-orig")
    return SUBTITLE_LANGS.index(base) if base in SUBTITLE_LANGS else len(SUBTITLE_LANGS)


def _pick_subtitle(subtitles: dict, auto: bool) -> Optional[dict]:
    langs = [lang for lang in subtitles or {} if lang not in SKIP_SUBTITLES]
    if auto:
        langs = [lang for lang in langs if lang.endswith("-orig")]
    for lang in sorted(langs, key=_lang_rank):
        for ext in SUBTITLE_EXTS:
            for sub in subtitles[lang]:
                if sub.get("ext") == ext:
                    return sub
    return None


def _lrc_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    return f"[{minutes:02d}:{seconds - minutes * 60:05.2f}]"


def _parse_timestamp(value: str) -> float:
    parts = value.replace(",", ".").split(":")
    seconds = 0.0
    for part in parts:
        seconds = seconds * 60 + float(part)
    return seconds


def _subtitle_lines(ext: str, data: str) -> list[tuple[float, str]]:
    if ext == "json3":
        lines = []
        for event in json.loads(data).get("events", []):
            text = "".join(seg.get("utf8", "") for seg in event.get("segs") or [])
            lines.append((event.get("tStartMs", 0) / 1000, text))
        return lines

    lines = []
    for block in re.split(r"\n\s*\n", data.replace("\r", "")):
        match = re.search(r"((?:\d+:)?\d{2}:\d{2}[.,]\d{3})\s*-->", block)
        if not match:
            continue
        text_lines = block[match.end() :].split("\n")[1:]
        text = re.sub(r"<[^>]+>", "", " ".join(text_lines))
        lines.append((_parse_timestamp(match.group(1)), text))
    return lines


def subtitle_to_lrc(ext: str, data: str) -> Optional[str]:
    result = []
    last_text = None
    for start, text in _subtitle_lines(ext, data):
        text = re.sub(r"<[^>]+>", " ", text)
        text = " ".join(text.split()).strip("♪♫ ")

        if not text or text == last_text:
            continue
        result.append(f"{_lrc_time(start)}{text}")
        last_text = text
    return "\n".join(result) or None


def _download_subtitle(sub: dict, headers: dict) -> Optional[str]:
    if sub.get("data"):
        return sub["data"]
    if not sub.get("url"):
        return None
    response = requests.get(sub["url"], headers=headers, timeout=10)
    response.raise_for_status()
    return response.text


def get_stream_lyrics(url: str) -> Optional[str]:
    with YoutubeDL({**BASE_OPTS, "ignore_no_formats_error": True}) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        return None
    headers = info.get("http_headers") or {}

    def from_subtitles(auto: bool) -> Optional[str]:
        source = info.get("automatic_captions" if auto else "subtitles")
        sub = _pick_subtitle(source, auto)
        if not sub:
            return None
        try:
            data = _download_subtitle(sub, headers)
            return subtitle_to_lrc(sub["ext"], data) if data else None
        except Exception as e:
            logger.warning(f"字幕下載失敗 {url}: {str(e)}")
            return None

    lyrics = from_subtitles(auto=False)
    if lyrics:
        return lyrics

    service_error = None
    if info.get("track") and info.get("artist"):
        try:
            lyrics = find_lyrics(
                info["track"], info["artist"], info.get("album"), info.get("duration")
            )
            if lyrics:
                return lyrics
        except LyricsServiceError as e:
            service_error = e

    lyrics = from_subtitles(auto=True)
    if not lyrics and service_error:
        raise service_error
    return lyrics


def save_stream_tracks(url: str, session: Session) -> list[StreamTrack]:
    infos = extract_stream_infos(url)
    tracks = []
    for info in infos:
        track = session.exec(
            select(StreamTrack).where(StreamTrack.url == info.url)
        ).first()
        if not track:
            track = StreamTrack(
                title=info.title,
                url=info.url,
                platform=info.platform,
                duration=info.duration,
                artist=info.artist,
                cover_art=info.thumbnail,
            )
            session.add(track)
        tracks.append(track)
    session.commit()
    for track in tracks:
        session.refresh(track)
    return tracks


class MusicStream:
    def __init__(self, url: str):
        self.url = url
        self.type: StreamPlatform = detect_url_type(url)
        self.yt_ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }
        self.bilibili_ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "m4a",
                    "preferredquality": "192",
                }
            ],
        }
        self.option = self._get_option()

    def _get_option(self) -> dict:
        match self.type:
            case StreamPlatform.YOUTUBE:
                return self.yt_ydl_opts
            case StreamPlatform.BILIBILI:
                return self.bilibili_ydl_opts
            case _:
                return self.yt_ydl_opts

    def get_stream_info(self) -> StreamInfo:
        try:
            infos = extract_stream_infos(self.url)
            return infos[0]
        except Exception as e:
            logger.error(f"取得stream失敗: {str(e)}")
            return StreamInfo(url="", title="")

    def download(self, output_path: str) -> bool:
        try:
            opts = self.option.copy()
            template = f"{output_path}/%(title)s.%(ext)s"

            postprocessors: list = list(opts.get("postprocessors", []))
            postprocessors.extend(
                [
                    {"key": "EmbedThumbnail"},
                    {
                        "key": "FFmpegMetadata",
                        "add_metadata": True,
                    },
                ]
            )
            opts.update(
                {
                    "outtmpl": template,
                    "writethumbnail": True,
                    "postprocessors": postprocessors,
                }
            )

            with YoutubeDL(opts) as ydl:
                ydl.download([self.url])
                return True
        except Exception as e:
            logger.error(f"下載失敗: {str(e)}")
            return False


if __name__ == "__main__":
    url = "https://www.bilibili.com/video/BV1BZq7YmEus/"
    print(extract_stream_infos(url))
    print(get_playable_stream(url))
