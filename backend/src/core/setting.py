from pydantic import BaseModel
from enum import Enum
from pathlib import Path


class StorageType(Enum):
    Music = "music"
    Video = "video"
    File = "file"


class Storage(BaseModel):
    type: StorageType
    Path: str | Path


class Setting(BaseModel):
    storages: list[Storage]
    scan_interval: int = 3600
