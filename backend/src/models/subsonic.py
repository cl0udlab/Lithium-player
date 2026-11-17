from typing import Optional
from sqlmodel import SQLModel, Field


class SubsonicSong(SQLModel, table=True):
    """Metadata linked to existing stream IDs, preserving playlists and audio cache."""
    track_id: int = Field(primary_key=True, foreign_key="streamtrack.id")
    source: str = Field(index=True)
    remote_album_id: str = Field(index=True)
    album_id: Optional[int] = Field(default=None, foreign_key="album.id", index=True)
    album: str = ""
    track_number: int = 0
    disc_number: int = 0
