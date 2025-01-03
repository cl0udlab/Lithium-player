from datetime import datetime
from typing import Optional
from sqlmodel import Field, Relationship, JSON
from enum import Enum, StrEnum
from .common import BaseModel, BasicFileModel
from .user import User, PlayHistory


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
    file: Optional["MusicTrackFile"] = Relationship(back_populates="track")

    # 演出者資訊
    artist: str = Field(index=True)
    album_artist: Optional[str] = Field(default=None, index=True)
    album: Optional[str] = Field(default=None)
    release_date: Optional[str] = Field(default=None)
    publisher: Optional[str] = Field(default=None)
    vocals: Optional[list[str]] = Field(default=None, sa_type=JSON)
    composer: Optional[list[str]] = Field(default=None, sa_type=JSON)
    arrangers: Optional[list[str]] = Field(default=None, sa_type=JSON)
    mixers: Optional[list[str]] = Field(default=None, sa_type=JSON)
    conductor: Optional[str] = Field(default=None)
    genre: Optional[str] = Field(default=None)

    # 額外資訊
    cover_art: Optional[str] = Field(default=None)
    lyrics: Optional[str] = Field(default=None)
    mood: Optional[str] = Field(default=None)
    bpm: Optional[int] = Field(default=None)
    track_number: Optional[int] = Field(default=None)
    disc_number: Optional[int] = Field(default=None)
    comment: Optional[str] = Field(default=None)

    album_id: Optional[int] = Field(
        default=None,
        foreign_key="album.id",
    )
    album_ref: Optional["Album"] = Relationship(
        back_populates="tracks",
    )
    play_history: list["PlayHistory"] = Relationship(
        back_populates="musictrack",
    )
    playlists: list["PlaylistTrack"] = Relationship(back_populates="track")


class MusicTrackFile(BasicFileModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    track_id: int = Field(foreign_key="musictrack.id")
    codec: AudioCodec
    bitrate: int
    sample_rate: int
    file_size: int
    audio_type: str
    track: MusicTrack = Relationship(back_populates="file")


class Album(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    album_artist: str = Field(index=True)
    publisher: Optional[str] = Field(default=None)
    genre: Optional[str] = Field(default=None)
    release_date: Optional[str] = Field(default=None)
    cover_art: Optional[str] = Field(default=None)
    total_tracks: Optional[int] = Field(default=None)
    total_discs: Optional[int] = Field(default=None)
    description: Optional[str] = Field(default=None)

    tracks: list["MusicTrack"] = Relationship(
        back_populates="album_ref",
    )


class StreamPlatform(StrEnum):
    YOUTUBE = "youtube"
    BILIBILI = "bilibili"
    SOUNDCLOUD = "soundcloud"
    UNKNOWN = "unknown"


class StreamTrack(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    url: str = Field(index=True)
    stream_url: Optional[str] = Field(default=None)
    platform: StreamPlatform
    duration: int
    artist: str = Field(index=True)
    release_year: Optional[int] = Field(default=None)
    publisher: Optional[str] = Field(default=None)
    composer: Optional[str] = Field(default=None)
    conductor: Optional[str] = Field(default=None)
    genre: Optional[str] = Field(default=None)
    cover_art: Optional[str] = Field(default=None)
    lyrics: Optional[str] = Field(default=None)

    play_history: list["PlayHistory"] = Relationship(
        back_populates="streamtrack",
    )
    playlists: list["PlaylistTrack"] = Relationship(back_populates="streamtrack")


class Playlist(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    user_id: int = Field(foreign_key="user.id")
    description: Optional[str] = Field(default=None)

    user: User = Relationship(back_populates="playlists")
    tracks: list["PlaylistTrack"] = Relationship(back_populates="playlist")


class Track_type(StrEnum):
    track = "track"
    stream = "stream"


class PlaylistTrack(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    playlist_id: int = Field(foreign_key="playlist.id")
    track_id: Optional[int] = Field(foreign_key="musictrack.id")
    streamtrack_id: Optional[int] = Field(foreign_key="streamtrack.id")
    position: int
    track_type: Track_type = Field(default=Track_type.track)
    added_at: datetime = Field(default_factory=datetime.now)
    playlist: "Playlist" = Relationship(back_populates="tracks")
    track: Optional["MusicTrack"] = Relationship(back_populates="playlists")
    streamtrack: Optional["StreamTrack"] = Relationship(back_populates="playlists")
