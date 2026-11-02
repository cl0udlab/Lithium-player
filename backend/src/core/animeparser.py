import json
import requests
from urllib.parse import quote
from models import Video
from pydantic import BaseModel
from typing import Union, Optional, overload
from core.logger import logger


HEADERS = {
    "User-Agent": "Lithium-player (https://github.com/cl0udlab/Lithium-player)",
    "Accept": "application/json",
}


class Images(BaseModel):
    small: str
    grid: str
    large: str
    medium: str
    common: str


class Tag(BaseModel):
    name: str
    count: int = 0
    total_count: int = 0


class ValueItem(BaseModel):
    v: str


class InfoboxItem(BaseModel):
    key: str
    value: Union[str, list[ValueItem]]


class Bangumi_Model(BaseModel):
    date: Optional[str] = None
    platform: str = ""
    images: Optional[Images] = None
    summary: str = ""
    name: str
    name_cn: str = ""
    tags: list[Tag] = []
    infobox: list[InfoboxItem] = []
    total_episodes: int = 0
    id: int
    eps: int = 0
    meta_tags: list[str] = []
    volumes: int = 0
    type: int = 2


@overload
def get_from_Bangumi(video: Video) -> Optional[Bangumi_Model]: ...


@overload
def get_from_Bangumi(title: str) -> Optional[Bangumi_Model]: ...


class Bangumi_SearchResult(BaseModel):
    id: int
    name: str
    name_cn: str = ""
    air_date: str = ""
    image: Optional[str] = None


def _https(url: Optional[str]) -> Optional[str]:
    if url and url.startswith("http://"):
        return "https://" + url[len("http://") :]
    return url


def search_Bangumi(title: str, max_results: int = 10) -> list[Bangumi_SearchResult]:
    try:
        searchurl = f"https://api.bgm.tv/search/subject/{quote(title)}?type=2&responseGroup=small&max_results={max_results}"
        r = requests.get(searchurl, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            logger.error(f"Bangumi API returned status code {r.status_code}")
            return []

        data = r.json()
        if not isinstance(data, dict) or not data.get("list"):
            logger.info(f"No results found for title: {title}")
            return []
        return [
            Bangumi_SearchResult(
                id=item["id"],
                name=item.get("name") or "",
                name_cn=item.get("name_cn") or "",
                air_date=item.get("air_date") or "",
                image=_https((item.get("images") or {}).get("large")),
            )
            for item in data["list"]
        ]
    except json.JSONDecodeError:
        logger.info(f"No results found for title: {title}")
        return []
    except Exception as e:
        logger.error(f"Bangumi API error: {str(e)}")
        return []


def get_Bangumi_subject(subject_id: int) -> Optional[Bangumi_Model]:
    """用 Bangumi subject id 取得完整資料"""
    try:
        r = requests.get(
            f"https://api.bgm.tv/v0/subjects/{subject_id}", headers=HEADERS, timeout=10
        )
        if r.status_code != 200:
            logger.error(
                f"Bangumi API detail request failed with status {r.status_code}"
            )
            return None
        subject = Bangumi_Model.model_validate(r.json())
        if subject.images:
            subject.images.large = _https(subject.images.large)
        return subject
    except Exception as e:
        logger.error(f"Bangumi API error: {str(e)}")
        return None


def get_from_Bangumi(video_or_title: Video | str) -> Optional[Bangumi_Model]:
    title = (
        video_or_title.title if isinstance(video_or_title, Video) else video_or_title
    )
    results = search_Bangumi(title)
    if not results:
        return None

    best = next((r for r in results if title in (r.name, r.name_cn)), results[0])
    return get_Bangumi_subject(best.id)
