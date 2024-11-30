from typing import Optional
from sqlmodel import Field, Relationship, ARRAY, Column, String
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


class VideoTagsLink(BaseModel, table=True):
    video_id: Optional[int] = Field(
        default=None, foreign_key="video.id", primary_key=True
    )
    tag_id: Optional[int] = Field(
        default=None, foreign_key="videotag.id", primary_key=True
    )


class AnimeTagsLink(BaseModel, table=True):
    series_id: Optional[int] = Field(
        default=None, foreign_key="animeseries.id", primary_key=True
    )
    tag_id: Optional[int] = Field(
        default=None, foreign_key="animetag.id", primary_key=True
    )


class VideoTag(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None)

    videos: list["Video"] = Relationship(
        back_populates="tags", link_model=VideoTagsLink
    )


class AnimeTag(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None)

    series: list["AnimeSeries"] = Relationship(
        back_populates="tags", link_model=AnimeTagsLink
    )


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
    subtitles: list[str] = Field(sa_column=Column(ARRAY(String)))
    audio_tracks: list[str] = Field(sa_column=Column(ARRAY(String)))
    thumbnail: Optional[bytes] = Field(default=None)

    series_id: Optional[int] = Field(default=None, foreign_key="animeseries.id")
    episode_number: Optional[int] = Field(default=None)

    series: Optional["AnimeSeries"] = Relationship(back_populates="episodes")
    tags: list[VideoTag] = Relationship(
        back_populates="videos", link_model=VideoTagsLink
    )


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
    tags: list[AnimeTag] = Relationship(
        back_populates="series", link_model=AnimeTagsLink
    )
    episodes: list[Video] = Relationship(back_populates="series")
