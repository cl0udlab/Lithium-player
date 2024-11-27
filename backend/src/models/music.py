from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, Relationship
from enum import Enum
from .common import BaseModel
from .user import User


class AudioCodec(str, Enum):
    MP3 = "mp3"
    FLAC = "flac"
    AAC = "aac"
    OGG = "ogg"
    OPUS = "opus"
    WAV = "wav"


class MusicTrack(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    duration: int
    codec: AudioCodec
    bitrate: int
    sample_rate: int
    file_size: int
    audio_type: str

    # 演出者資訊
    artist: str = Field(index=True)
    album_artist: Optional[str] = Field(default=None, index=True)
    album: Optional[str] = Field(default=None)
    release_year: Optional[int] = Field(default=None)
    publisher: Optional[str] = Field(default=None)
    composer: Optional[str] = Field(default=None)
    conductor: Optional[str] = Field(default=None)
    genre: Optional[str] = Field(default=None)

    # 額外資訊
    cover_art: Optional[bytes] = Field(default=None)
    lyrics: Optional[str] = Field(default=None)
    mood: Optional[str] = Field(default=None)
    bpm: Optional[int] = Field(default=None)
    track_number: Optional[int] = Field(default=None)
    disc_number: Optional[int] = Field(default=None)
    comment: Optional[str] = Field(default=None)

    album_ref: Optional["Album"] = Relationship(back_populates="tracks")


class Album(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    album_artist: str = Field(index=True)
    publisher: Optional[str] = Field(default=None)
    genre: Optional[str] = Field(default=None)
    release_year: Optional[int] = Field(default=None)
    cover_art: Optional[bytes] = Field(default=None)
    total_tracks: Optional[int] = Field(default=None)
    total_discs: Optional[int] = Field(default=None)
    description: Optional[str] = Field(default=None)

    tracks: List[MusicTrack] = Relationship(back_populates="album_ref")


class Playlist(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    user_id: int = Field(foreign_key="user.id")
    description: Optional[str] = Field(default=None)

    user: User = Relationship(back_populates="playlists")
    tracks: List["PlaylistTrack"] = Relationship(back_populates="playlist")


class PlaylistTrack(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    playlist_id: int = Field(foreign_key="playlist.id")
    track_id: int = Field(foreign_key="musictrack.id")
    position: int
    added_at: datetime = Field(default_factory=datetime.utcnow)
