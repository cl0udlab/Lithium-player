from enum import StrEnum
from pathlib import Path
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session
from core.setting import Storage, StorageType, update_setting
from typing import Dict, List

from db import get_db
import os


setting_router = APIRouter(prefix="/setting", tags=["setting"])

SessionDep = Annotated[Session, Depends(get_db)]


@setting_router.get("/dir")
async def get_system_dir(path: str = "/") -> dict:
    try:
        items = os.listdir(path)
        files = []
        dirs = []

        for item in items:
            full_path = os.path.join(path, item)
            if os.path.isfile(full_path):
                files.append(item)
            elif os.path.isdir(full_path):
                dirs.append(item)

    except NotADirectoryError:
        return {"error": "該路徑不是目錄"}
    except FileNotFoundError:
        return {"error": "找不到路徑"}
    except PermissionError:
        return {"error": "沒有權限訪問該路徑"}

    return {"files": files, "dirs": dirs, "path": path}


class LogLevel(StrEnum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class StorageUpdate(BaseModel):
    type: StorageType
    LangCode: str
    path: str


class SettingUpdate(BaseModel):
    storage: Optional[List[StorageUpdate]] = None
    scan_interval: Optional[int] = Field(None, ge=60)
    log_level: Optional[LogLevel] = None
    tmd_api_key: Optional[str] = None


@setting_router.post("/update")
async def update_system_setting(update: SettingUpdate) -> Dict:
    try:
        updates = {}

        if update.storage is not None:
            updates["storage"] = [
                Storage(type=s.type, LangCode=s.LangCode, path=Path(s.path))
                for s in update.storage
            ]

        if update.scan_interval is not None:
            updates["scan_interval"] = update.scan_interval

        if update.log_level is not None:
            updates["log_level"] = update.log_level

        if update.tmd_api_key is not None:
            updates["tmd_api_key"] = update.tmd_api_key

        setting = update_setting(updates)
        return {"message": "設定已更新", "setting": setting.model_dump()}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
