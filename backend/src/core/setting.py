from pydantic import BaseModel
from enum import StrEnum
from pathlib import Path
from typing import Any
import json

SETTTING_PATH = Path("data") / "setting.json"

class StorageType(StrEnum):
    MUSIC = "music"
    VIDEO = "video"
    FILE = "file"


class Storage(BaseModel):
    type: StorageType
    path: Path

    def model_dump(self, **kwargs) -> dict[str, Any]:
        data = super().model_dump(**kwargs)
        data["path"] = str(data["path"])
        return data


class Setting(BaseModel):
    storages: list[Storage] = []
    scan_interval: int = 3600
    log_level: str = "info"

    model_config = {
        "json_encoders": {Path: str, StorageType: str},
        "use_enum_values": True,
    }

    def model_dump(self, **kwargs) -> dict[str, Any]:
        data = super().model_dump(**kwargs)
        data["storages"] = [storage.model_dump(**kwargs) for storage in self.storages]
        return data

def load_setting() -> Setting:
    with open(SETTTING_PATH) as f:
        return Setting.model_validate_json(json.load(f))