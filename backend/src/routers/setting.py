from typing import Annotated
from fastapi import APIRouter, Depends
from sqlmodel import Session

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
