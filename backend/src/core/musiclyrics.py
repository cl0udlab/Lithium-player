import requests
from models import MusicTrack
from typing import Optional, overload

HEADERS = {"User-Agent": "Lithium-player (https://github.com/cl0udlab/Lithium-player)"}


@overload
def get_lrclib(music: MusicTrack) -> Optional[str]: ...


@overload
def get_lrclib(album: str, artist: str, title: str) -> Optional[str]: ...


def get_lrclib(arg1, arg2=None, arg3=None) -> Optional[str]:
    if isinstance(arg1, MusicTrack):
        music = arg1
        response = requests.get(
            f"https://lrclib.net/api/get?artist_name={music.album_artist}&track_name={music.title}&album_name={music.album}",
            headers=HEADERS,
        )
    else:
        album, artist, title = arg1, arg2, arg3
        response = requests.get(
            f"https://lrclib.net/api/get?artist_name={artist}&track_name={title}&album_name={album}",
            headers=HEADERS,
        )

    lyrics = response.json()
    if "statusCode" in lyrics and lyrics["statusCode"] == 404:
        return None
    if "syncedLyrics" not in lyrics:
        return None
    return lyrics["syncedLyrics"]
