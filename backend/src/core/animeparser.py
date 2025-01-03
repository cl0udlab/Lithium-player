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
    count: int
    total_cont: int


class ValueItem(BaseModel):
    v: str


class InfoboxItem(BaseModel):
    key: str
    value: Union[str, list[ValueItem]]


class Bangumi_Model(BaseModel):
    date: str
    platform: str
    images: Images
    summary: str
    name: str
    name_cn: str
    tags: list[Tag]
    infobox: list[InfoboxItem]
    total_episodes: int
    id: int
    eps: int
    meta_tags: list[str]
    volumes: int
    type: int


@overload
def get_from_Bangumi(video: Video) -> Optional[Bangumi_Model]: ...


@overload
def get_from_Bangumi(title: str) -> Optional[Bangumi_Model]: ...


def get_from_Bangumi(video_or_title: Video | str) -> Optional[Bangumi_Model]:
    """搜尋 Bangumi API"""
    try:
        title = (
            video_or_title.title
            if isinstance(video_or_title, Video)
            else video_or_title
        )

        searchurl = f"https://api.bgm.tv/search/subject/{quote(title)}?type=2&responseGroup=small"
        r = requests.get(searchurl, headers=HEADERS)
        if r.status_code != 200:
            logger.error(f"Bangumi API returned status code {r.status_code}")
            return None

        data = r.json()
        if not data or not data.get("list") or len(data["list"]) == 0:
            logger.info(f"No results found for title: {title}")
            return None

        id = data["list"][0]["id"]
        idsearchurl = f"https://api.bgm.tv/v0/subjects/{id}"
        r = requests.get(idsearchurl, headers=HEADERS)
        if r.status_code != 200:
            logger.error(
                f"Bangumi API detail request failed with status {r.status_code}"
            )
            return None

        return Bangumi_Model.model_validate(r.json())
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Bangumi API response: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Bangumi API error: {str(e)}")
        return None
