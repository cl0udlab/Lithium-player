from pydantic import BaseModel
import requests
from core.logger import logger
from typing import Optional, Any


BASE_URL = "https://musicbrainz.org/ws/2"
HEADERS = {
    "User-Agent": "Lithium-player/0.0.1 (https://github.com/cl0udlab/Lithium-player)",
    "Accept": "application/json",
}


class ArtistInfo(BaseModel):
    name: str
    name_sort: Optional[str] = None
    type: Optional[str] = None


class Version(BaseModel):
    title: str
    length: Optional[int] = None
    type: str
    video: bool = False


class TrackInfo(BaseModel):
    title: str
    length: Optional[int] = None
    first_release_date: Optional[str] = None
    id: str
    artist: str
    vocals: list[ArtistInfo] = []
    arrangers: list[str] = []
    mixers: list[str] = []
    versions: list[Version] = []
    cover_art: Optional[str] = None


class AlbumTrack(BaseModel):
    title: str
    id: str
    length: int = 0
    position: int = 0
    first_release_date: Optional[str] = None


class AlbumInfo(BaseModel):
    title: str
    artist: str
    release_date: Optional[str] = None
    barcode: Optional[str] = None
    tracks: list[AlbumTrack] = []


def search_track(title: str, artist: str) -> Optional[dict[str, Any]]:
    if not title or not artist:
        return None
    try:
        params = {"query": f"recording:{title} AND artist:{artist}", "fmt": "json"}
        response = requests.get(f"{BASE_URL}/recording", headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        if not data.get("recordings"):
            logger.info(f"找不到歌曲: {title}")
            return None

        recording_id = data["recordings"][0]["id"]
        detail_params = {
            "fmt": "json",
            "inc": "artists+artist-credits+artist-rels+work-rels+recording-rels+releases",
        }
        detail_response = requests.get(
            f"{BASE_URL}/recording/{recording_id}",
            headers=HEADERS,
            params=detail_params,
        )
        detail_response.raise_for_status()
        recording = detail_response.json()
        if "releases" in recording and recording["releases"]:
            release_id = recording["releases"][0]["id"]
            cover_art_response = requests.get(
                f"https://coverartarchive.org/release/{release_id}", headers=HEADERS
            )
            if cover_art_response.status_code == 200:
                cover_art_data = cover_art_response.json()
                if cover_art_data.get("images"):
                    recording["cover_art"] = cover_art_data["images"][0]["image"]

        return recording

    except requests.exceptions.RequestException as e:
        logger.error(f"API請求錯誤: {str(e)}")
        return None
    except KeyError as e:
        logger.error(f"資料解析錯誤: {str(e)}")
        return None


def parse_track_info(data: dict) -> Optional[TrackInfo]:
    if not data:
        return None
    try:
        relations = data.get("relations", [])
        vocals = []
        arrangers = []
        mixers = []
        versions = []

        for relation in relations:
            rel_type = relation.get("type")
            if rel_type == "vocal":
                artist_info = relation.get("artist", {})
                vocals.append(
                    ArtistInfo(
                        name=artist_info.get("name", ""),
                        name_sort=artist_info.get("sort-name"),
                        type=artist_info.get("type"),
                    )
                )
            elif rel_type == "arranger":
                artist_info = relation.get("artist", {})
                arrangers.append(artist_info.get("name", ""))
            elif rel_type == "mix":
                artist_info = relation.get("artist", {})
                mixers.append(artist_info.get("name", ""))
            elif rel_type in ["edit", "karaoke", "music video"]:
                rec = relation.get("recording", {})
                if rec:
                    versions.append(
                        Version(
                            title=rec.get("title", ""),
                            length=rec.get("length"),
                            type=rel_type,
                            video=rec.get("video", False),
                        )
                    )

        return TrackInfo(
            title=data.get("title", ""),
            length=data.get("length"),
            first_release_date=data.get("first-release-date"),
            id=data.get("id", ""),
            artist=data["artist-credit"][0]["name"],
            vocals=vocals,
            arrangers=arrangers,
            mixers=mixers,
            versions=versions,
            cover_art=data.get("cover_art"),
        )

    except Exception as e:
        logger.error(f"解析歌曲資訊失敗: {str(e)}")
        return None


def search_album(album: str, artist: str) -> Optional[dict[str, Any]]:
    if not album or not artist:
        return None
    try:
        params = {"query": f"release:{album} AND artist:{artist}", "fmt": "json"}
        response = requests.get(f"{BASE_URL}/release", headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        if data["releases"] and len(data["releases"]) > 0:
            release_id = data["releases"][0]["id"]
            response = requests.get(
                f"{BASE_URL}/release/{release_id}",
                headers=HEADERS,
                params={"fmt": "json", "inc": "recordings+artists"},
            )
            response.raise_for_status()
            return response.json()
        logger.info(f"找不到專輯: {album}")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API請求錯誤: {str(e)}")
        return None


def parse_album_info(data: dict) -> Optional[AlbumInfo]:
    if not data:
        return None
    try:
        tracks = []
        for media in data.get("media", []):
            for track in media.get("tracks", []):
                recording = track.get("recording", {})
                tracks.append(
                    AlbumTrack(
                        title=track.get("title", ""),
                        id=recording.get("id", ""),
                        length=recording.get("length", 0),
                        position=track.get("position", 0),
                        first_release_date=recording.get("first-release-date"),
                    )
                )

        return AlbumInfo(
            title=data.get("title", ""),
            artist=data["artist-credit"][0]["name"],
            release_date=data.get("date"),
            barcode=data.get("barcode"),
            tracks=tracks,
        )

    except Exception as e:
        logger.error(f"解析專輯資訊失敗: {str(e)}")
        return None


if __name__ == "__main__":
    print(parse_track_info(search_track("ファタール - Fatal", "GEMN")))
    # print(parse_album_info(search_album("ファタール - Fatal", "GEMN")))
