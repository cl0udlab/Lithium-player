from typing import Optional, List, Dict
from sqlmodel import Field, Relationship
from enum import Enum
from .common import BaseModel


class VideoCodec(str, Enum):
    H264 = "h264"
    H265 = "h265"
    VP9 = "vp9"
    AV1 = "av1"
    Unknown = "unknown"

class VideoFormat(str, Enum):
    MP4 = "mp4"
    MKV = "mkv"
    WEBM = "webm"
    AVI = "avi"
    FLV = "flv"
    MOV = "mov"
    WMV = "wmv"


class Video(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    duration: int
    file_size: int
    codec: VideoCodec
    format: VideoFormat
    width: int
    height: int
    frame_rate: float

    description: Optional[str] = Field(default=None)
    subtitles: List[Dict] = Field(default_factory=list)
    audio_tracks: List[Dict] = Field(default_factory=list)
    thumbnail: Optional[bytes] = Field(default=None)

    series_id: Optional[int] = Field(default=None, foreign_key="animeseries.id")
    episode_number: Optional[int] = Field(default=None)

    series: Optional["AnimeSeries"] = Relationship(back_populates="episodes")


class AnimeSeries(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    original_title: Optional[str] = Field(default=None)
    release_year: int
    author: Optional[str] = Field(default=None)
    studio: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    season_number: Optional[int] = Field(default=None)
    total_episodes: Optional[int] = Field(default=None)
    cover_image: Optional[bytes] = Field(default=None)
    tags: Optional[List[str]] = Field(default_factory=list)

    episodes: List[Video] = Relationship(back_populates="series")
