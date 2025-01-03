from pydantic import BaseModel, field_validator
from enum import StrEnum
from pathlib import Path
from typing import Any
import json

SETTTING_PATH = Path("data") / "settings.json"


class StorageType(StrEnum):
    MUSIC = "music"
    VIDEO = "video"
    FILE = "file"


LANGCODES = {
    "zh-CN": {"Country": "中国", "Language": "简体中文"},
    "zh-TW": {"Country": "臺灣", "Language": "繁體中文"},
    "en-US": {"Country": "United States ", "Language": "English"},
    "ja-JP": {"Country": "日本", "Language": "日本語"},
    "ko-KR": {"Country": "대한민국", "Language": "한국어"},
}


class Storage(BaseModel):
    type: StorageType
    LangCode: str
    path: Path

    @field_validator("LangCode")
    @classmethod
    def validate_lang_code(cls, value: str) -> str:
        if value not in LANGCODES:
            raise ValueError(
                f'語言代碼必須是以下其中之一: {", ".join(LANGCODES.keys())}'
            )
        return value

    def model_dump(self, **kwargs) -> dict[str, Any]:
        data = super().model_dump(**kwargs)
        data["path"] = str(data["path"])
        return data


class Setting(BaseModel):
    storages: list[Storage] = []
    scan_interval: int = 3600
    log_level: str = "info"
    tmd_api_key: str = ""

    model_config = {
        "json_encoders": {Path: str, StorageType: str},
        "use_enum_values": True,
    }

    def model_dump(self, **kwargs) -> dict[str, Any]:
        data = super().model_dump(**kwargs)
        data["storages"] = [storage.model_dump(**kwargs) for storage in self.storages]
        return data


def load_setting() -> Setting:
    """載入設定檔"""
    try:
        with open(SETTTING_PATH) as f:
            data = json.load(f)
            return Setting.model_validate(data)
    except FileNotFoundError:
        return Setting()


def save_setting(setting: Setting) -> None:
    """儲存設定到檔案"""
    try:
        SETTTING_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTTING_PATH, "w", encoding="utf-8") as f:
            json.dump(setting.model_dump(), f, ensure_ascii=False, indent=2)

    except Exception as e:
        raise ValueError(f"儲存設定失敗: {str(e)}")


def update_setting(updates: dict[str, Any]) -> Setting:
    """更新設定"""
    try:
        current_setting = load_setting()
        setting_dict = current_setting.model_dump()
        setting_dict.update(updates)
        new_setting = Setting.model_validate(setting_dict)
        save_setting(new_setting)
        return new_setting

    except Exception as e:
        raise ValueError(f"更新設定失敗: {str(e)}")
