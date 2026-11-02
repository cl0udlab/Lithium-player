import re
import xml.etree.ElementTree as ET
from typing import Optional
from core.logger import logger
from .base import (
    DURATION_TOLERANCE,
    LyricLine,
    LyricWord,
    Lyrics,
    LyricsProvider,
    LyricsQuery,
    artist_matches,
    request_json,
    strip_version,
    title_matches,
)

AMLL_URL = "https://api.amll.dev/v1/lyrics"
TTM_NS = "http://www.w3.org/ns/ttml#metadata"
ITUNES_NS = "http://music.apple.com/lyric-ttml-internal"
MAX_CANDIDATES = 3


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_ttml_time(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    value = value.strip()
    try:
        if value.endswith("ms"):
            return float(value[:-2]) / 1000
        if value.endswith("s"):
            return float(value[:-1])
        total = 0.0
        for part in value.split(":"):
            total = total * 60 + float(part)
        return total
    except ValueError:
        return None


def _parse_line(el: ET.Element) -> LyricLine:
    words: list[LyricWord] = []
    translation = romanization = background = None
    plain = el.text or ""
    for child in el:
        role = child.get(f"{{{TTM_NS}}}role")
        text = "".join(child.itertext())
        if role == "x-translation":
            translation = translation or text.strip()
        elif role == "x-roman":
            romanization = romanization or text.strip()
        elif role == "x-bg":
            background = _parse_line(child)
        elif _local(child.tag) == "span":
            start = parse_ttml_time(child.get("begin"))
            end = parse_ttml_time(child.get("end"))
            if start is not None:
                words.append(LyricWord(start, end if end is not None else start, text))
            elif words:
                words[-1].text += text
            plain += text

        if child.tail:
            plain += child.tail
            if words and role is None:
                tail = " " if child.tail.isspace() else child.tail
                if not (tail == " " and words[-1].text.endswith(" ")):
                    words[-1].text += tail

    start = parse_ttml_time(el.get("begin"))
    end = parse_ttml_time(el.get("end"))
    if start is None and words:
        start = words[0].start
    if end is None and words:
        end = words[-1].end
    text = "".join(w.text for w in words) if words else plain
    return LyricLine(
        start=start or 0.0,
        end=end,
        text=re.sub(r"\s+", " ", text).strip(),
        words=words,
        translation=translation or None,
        romanization=romanization or None,
        agent=el.get(f"{{{TTM_NS}}}agent"),
        background=background,
    )


def _head_texts(root: ET.Element, kind: str) -> dict[str, str]:
    result = {}
    for el in root.iter():
        if _local(el.tag) != kind:
            continue
        for text in el:
            key = text.get("for")
            if _local(text.tag) == "text" and key and key not in result:
                result[key] = "".join(text.itertext()).strip()
    return result


def parse_ttml(source: str, ttml: str) -> Optional[Lyrics]:
    if re.search(r"<!(DOCTYPE|ENTITY)", ttml, re.I):
        return None
    try:
        root = ET.fromstring(ttml)
    except ET.ParseError as e:
        logger.warning(f"{source} TTML 解析失敗: {str(e)}")
        return None

    translations = _head_texts(root, "translation")
    romanizations = _head_texts(root, "transliteration")
    lines = []
    for el in root.iter():
        if _local(el.tag) != "p":
            continue
        line = _parse_line(el)
        key = el.get(f"{{{ITUNES_NS}}}key")
        if key:
            line.translation = line.translation or translations.get(key)
            line.romanization = line.romanization or romanizations.get(key)
        if line.text:
            lines.append(line)
    if not lines:
        return None
    lines.sort(key=lambda line: line.start)
    return Lyrics(source=source, lines=lines)


class AmllProvider(LyricsProvider):
    name = "amll"

    def _candidates(self, query: LyricsQuery, retries: int) -> list[dict]:
        artist = query.artist and re.split(r"[,/&;、]", query.artist)[0].strip()
        for title in dict.fromkeys([query.title, strip_version(query.title)]):
            params = {"musicName": title, "pageSize": 50}
            if artist:
                params["artistName"] = artist
            data = request_json(
                "GET", f"{AMLL_URL}/search", retries, self.name, params=params
            )
            items = ((data or {}).get("data") or {}).get("items") or []
            matched = [
                item
                for item in items
                if any(
                    title_matches(query.title, n) for n in item.get("musicNames") or []
                )
                and artist_matches(query.artist, item.get("artistNames") or [])
            ]
            if matched:
                return matched[:MAX_CANDIDATES]
        return []

    def search(self, query: LyricsQuery, retries: int) -> Optional[Lyrics]:
        for item in self._candidates(query, retries):
            data = request_json(
                "GET", f"{AMLL_URL}/get", retries, self.name, params={"id": item["id"]}
            )
            ttml = ((data or {}).get("data") or {}).get("lyrics")
            lyrics = parse_ttml(self.name, ttml) if ttml else None
            if not lyrics:
                continue
            last = lyrics.lines[-1].end or lyrics.lines[-1].start
            if query.duration and last > query.duration + DURATION_TOLERANCE:
                continue
            return lyrics
        return None
