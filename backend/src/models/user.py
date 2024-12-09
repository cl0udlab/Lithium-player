from typing import Optional, TYPE_CHECKING
from sqlalchemy import CheckConstraint
from sqlmodel import Field, Relationship, Column, JSON
from enum import Enum
from datetime import datetime
from .common import BaseModel

if TYPE_CHECKING:
    from .music import Playlist, MusicTrack
    from .video import Video


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class UserLikes(BaseModel, table=True):
    user_id: Optional[int] = Field(
        default=None, foreign_key="user.id", primary_key=True
    )
    track_id: Optional[int] = Field(
        default=None, foreign_key="musictrack.id", primary_key=True
    )


class UserDislikes(BaseModel, table=True):
    user_id: Optional[int] = Field(
        default=None, foreign_key="user.id", primary_key=True
    )
    track_id: Optional[int] = Field(
        default=None, foreign_key="musictrack.id", primary_key=True
    )


class User(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    role: UserRole = Field(default=UserRole.USER)
    preferences: dict = Field(default_factory=dict, sa_column=Column(JSON))

    likelist: list["MusicTrack"] = Relationship(
        link_model=UserLikes,
        sa_relationship_kwargs={"lazy": "selectin", "back_populates": None},
    )
    dislikelist: list["MusicTrack"] = Relationship(
        link_model=UserDislikes,
        sa_relationship_kwargs={"lazy": "selectin", "back_populates": None},
    )

    playlists: list["Playlist"] = Relationship(back_populates="user")
    play_history: list["PlayHistory"] = Relationship(
        back_populates="user", sa_relationship_kwargs={"lazy": "selectin"}
    )


class PlayHistory(BaseModel, table=True):
    __table_args__ = (
        CheckConstraint(
            "(track_id IS NOT NULL AND video_id IS NULL) OR (track_id IS NULL AND video_id IS NOT NULL)",
            name="check_track_or_video",
        ),
    )
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    track_id: Optional[int] = Field(foreign_key="musictrack.id", default=None)
    video_id: Optional[int] = Field(foreign_key="video.id", default=None)
    played_at: datetime = Field(default_factory=datetime.now)
    musictrack: Optional["MusicTrack"] = Relationship(
        back_populates="play_history",
        sa_relationship_kwargs={"lazy": "joined"},
    )
    video: Optional["Video"] = Relationship(
        back_populates="play_history",
        sa_relationship_kwargs={"lazy": "joined"},
    )
    user: "User" = Relationship(back_populates="play_history")
