from typing import Optional, List, Dict
from sqlmodel import Field, Relationship
from enum import Enum
from .common import BaseModel
from .music import Playlist


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class User(BaseModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    role: UserRole = Field(default=UserRole.USER)
    preferences: Dict = Field(default={})

    playlists: List["Playlist"] = Relationship(back_populates="user")
