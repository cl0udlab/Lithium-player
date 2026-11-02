import os
from typing import Optional
from core.logger import logger
from .amll import AmllProvider
from .base import (
    LyricLine,
    LyricWord,
    Lyrics,
    LyricsProvider,
    LyricsQuery,
    LyricsServiceError,
)
from .lrclib import LrclibProvider
from .qqmusic import QQMusicProvider

__all__ = [
    "LyricLine",
    "LyricWord",
    "Lyrics",
    "LyricsProvider",
    "LyricsQuery",
    "LyricsServiceError",
    "PROVIDERS",
    "find_lyrics",
    "get_lyrics",
    "search_lyrics",
]

AVAILABLE_PROVIDERS: dict[str, LyricsProvider] = {
    p.name: p for p in (QQMusicProvider(), AmllProvider(), LrclibProvider())
}
# 優先順序, 排前面的沒有歌詞才問下一個 (不是比誰先回應)
# 可用 LYRICS_PROVIDERS=qqmusic,amll,lrclib 調整
DEFAULT_PRIORITY = "qqmusic,amll,lrclib"
PROVIDERS: list[LyricsProvider] = [
    AVAILABLE_PROVIDERS[name.strip()]
    for name in os.getenv("LYRICS_PROVIDERS", DEFAULT_PRIORITY).split(",")
    if name.strip() in AVAILABLE_PROVIDERS
]


def search_lyrics(
    query: LyricsQuery,
    retries: int = 6,
    providers: Optional[list[LyricsProvider]] = None,
) -> Optional[Lyrics]:
    """回傳完整結構 (逐字時間, 翻譯, 羅馬音...), 全部來源都暫時無法使用時丟 LyricsServiceError"""
    if not query.title:
        return None
    last_error = None
    for provider in PROVIDERS if providers is None else providers:
        try:
            lyrics = provider.search(query, retries)
        except LyricsServiceError as e:
            logger.warning(f"{provider.name} 暫時無法使用: {str(e)}")
            last_error = e
            continue
        except Exception as e:
            logger.warning(f"{provider.name} 查詢失敗: {str(e)}")
            continue
        if lyrics:
            return lyrics
    if last_error:
        raise last_error
    return None


def find_lyrics(
    title: Optional[str],
    artist: Optional[str],
    album: Optional[str] = None,
    duration: Optional[float] = None,
    retries: int = 6,
) -> Optional[str]:
    lyrics = search_lyrics(LyricsQuery(title or "", artist, album, duration), retries)
    return lyrics.to_lrc() if lyrics else None


def get_lyrics(album: str, artist: str, title: str, duration=None) -> Optional[str]:
    try:
        return find_lyrics(title, artist, album, duration, retries=3)
    except Exception as e:
        logger.warning(f"歌詞查詢失敗, 播放時再重試: {str(e)}")
        return None
