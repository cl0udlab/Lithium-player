import bisect
import re
import time
import unicodedata
import requests
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from core.logger import logger

HEADERS = {"User-Agent": "Lithium-player (https://github.com/cl0udlab/Lithium-player)"}
DURATION_TOLERANCE = 5

IGNORED_TEXTS = {"//", "QQ音乐享有本翻译作品的著作权"}


class LyricsServiceError(Exception): ...


@dataclass
class LyricsQuery:
    title: str
    artist: Optional[str] = None
    album: Optional[str] = None
    duration: Optional[float] = None


@dataclass
class LyricWord:
    start: float
    end: float
    text: str


@dataclass
class LyricLine:
    """一句歌詞, words 為空代表來源只有逐句時間"""

    start: float
    text: str
    end: Optional[float] = None
    words: list[LyricWord] = field(default_factory=list)
    translation: Optional[str] = None
    romanization: Optional[str] = None

    agent: Optional[str] = None

    background: Optional["LyricLine"] = None


@dataclass
class Lyrics:
    source: str
    lines: list[LyricLine]

    @property
    def word_synced(self) -> bool:
        return any(line.words for line in self.lines)

    def to_lrc(self, translation: bool = True) -> str:
        out = []
        for line in self.lines:
            tag = format_lrc_time(line.start)
            out.append(f"{tag}{line.text}")
            if translation and line.translation:
                out.append(f"{tag}{line.translation}")
        return "\n".join(out)


class LyricsProvider(ABC):
    name: str

    @abstractmethod
    def search(self, query: LyricsQuery, retries: int) -> Optional[Lyrics]:
        """找不到回傳 None, 服務暫時無法使用時丟 LyricsServiceError"""


def request_json(
    method: str, url: str, retries: int, name: str, **kwargs
) -> Optional[dict | list]:
    kwargs.setdefault("headers", HEADERS)
    kwargs.setdefault("timeout", 10)
    last_error = None
    for attempt in range(retries):
        if attempt:
            time.sleep(min(attempt * 1.5, 5))
        try:
            response = requests.request(method, url, **kwargs)
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            continue
        if response.status_code >= 500 or response.status_code == 429:
            last_error = f"HTTP {response.status_code}"
            continue
        if response.status_code >= 400:
            if response.status_code != 404:
                logger.warning(f"{name} {url} HTTP {response.status_code}")
            return None
        try:
            return response.json()
        except ValueError:
            last_error = "回應不是 JSON"
            continue
    raise LyricsServiceError(f"{name} {url} 失敗 ({retries} 次): {last_error}")


def strip_version(title: str) -> str:
    return re.sub(r"\s*[\(（\[【][^\)）\]】]*[\)）\]】]\s*$", "", title).strip()


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    return "".join(c for c in text if c.isalnum())


def title_matches(title: str, candidate: str) -> bool:
    a, b = normalize(title), normalize(candidate)
    return bool(a) and (
        a == b or normalize(strip_version(title)) == normalize(strip_version(candidate))
    )


def artist_matches(artist: Optional[str], candidates: list[str]) -> bool:
    if not artist:
        return True
    names = [normalize(c) for c in candidates if normalize(c)]
    for part in re.split(r"[,/&;、]|\bfeat\.?|\bft\.?", artist, flags=re.I):
        part = normalize(part)
        if part and any(part in name or name in part for name in names):
            return True
    return False


def format_lrc_time(seconds: float) -> str:
    centis = round(max(seconds, 0) * 100)
    return f"[{centis // 6000:02d}:{centis // 100 % 60:02d}.{centis % 100:02d}]"


LRC_TIME = re.compile(r"\[(\d{1,3}):(\d{1,2}(?:[.:]\d{1,3})?)\]")


def parse_lrc(text: str) -> list[tuple[float, str]]:
    entries = []
    for line in text.splitlines():
        tags = LRC_TIME.findall(line)
        if not tags:
            continue
        content = LRC_TIME.sub("", line).strip()
        for minutes, seconds in tags:
            entries.append(
                (int(minutes) * 60 + float(seconds.replace(":", ".")), content)
            )
    entries.sort(key=lambda e: e[0])
    return entries


def lyrics_from_lrc(
    source: str, lyric: str, translation: Optional[str] = None
) -> Optional[Lyrics]:
    lines: list[LyricLine] = []
    for start, text in parse_lrc(lyric):
        if lines and abs(lines[-1].start - start) < 0.01:
            if text and not lines[-1].translation:
                lines[-1].translation = text
            continue
        lines.append(LyricLine(start=start, text=text))
    if not any(line.text for line in lines):
        return None

    if translation:
        attach_by_time(lines, parse_lrc(translation), "translation")
    return Lyrics(source=source, lines=lines)


def attach_by_time(
    lines: list[LyricLine],
    entries: list[tuple[float, str]],
    attr: str,
    tolerance: float = 0.5,
) -> None:
    starts = [line.start for line in lines]
    for time_, text in entries:
        if not text or text in IGNORED_TEXTS:
            continue
        i = bisect.bisect_left(starts, time_)
        nearest = min(
            (j for j in (i - 1, i) if 0 <= j < len(lines)),
            key=lambda j: abs(starts[j] - time_),
            default=None,
        )
        if nearest is None or abs(starts[nearest] - time_) > tolerance:
            continue
        line = lines[nearest]
        if line.text and not getattr(line, attr):
            setattr(line, attr, text)
