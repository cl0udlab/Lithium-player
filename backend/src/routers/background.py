from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from auth import get_user
from models import User

background_router = APIRouter(prefix="/background", tags=["background"])

BACKGROUND_DIR = Path("data/backgrounds")
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
VIDEO_EXTS = {".mp4", ".webm"}
MAX_SIZE = 500 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024


class BackgroundInfo(BaseModel):
    id: str
    type: str
    size: int


def _info(path: Path) -> BackgroundInfo:
    return BackgroundInfo(
        id=path.name,
        type="video" if path.suffix in VIDEO_EXTS else "image",
        size=path.stat().st_size,
    )


def _resolve(background_id: str) -> Path:
    path = (BACKGROUND_DIR / background_id).resolve()
    if path.parent != BACKGROUND_DIR.resolve() or not path.is_file():
        raise HTTPException(status_code=404, detail="找不到背景")
    return path


@background_router.get("", response_model=list[BackgroundInfo])
async def list_backgrounds():
    if not BACKGROUND_DIR.exists():
        return []
    files = [
        p
        for p in BACKGROUND_DIR.iterdir()
        if p.is_file() and p.suffix in IMAGE_EXTS | VIDEO_EXTS
    ]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [_info(p) for p in files]


@background_router.post("", response_model=BackgroundInfo)
async def upload_background(file: UploadFile, user: User = Depends(get_user)):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in IMAGE_EXTS | VIDEO_EXTS:
        raise HTTPException(
            status_code=400, detail="只支援 jpg / png / webp / gif / avif / mp4 / webm"
        )

    BACKGROUND_DIR.mkdir(parents=True, exist_ok=True)
    path = BACKGROUND_DIR / f"{uuid4()}{ext}"
    size = 0
    try:
        with open(path, "wb") as f:
            while chunk := await file.read(CHUNK_SIZE):
                size += len(chunk)
                if size > MAX_SIZE:
                    raise HTTPException(status_code=413, detail="檔案太大 (上限 500MB)")
                f.write(chunk)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return _info(path)


@background_router.get("/{background_id}")
async def get_background(background_id: str):
    return FileResponse(_resolve(background_id))


@background_router.delete("/{background_id}")
async def delete_background(background_id: str, user: User = Depends(get_user)):
    _resolve(background_id).unlink()
    return {"message": "背景已刪除"}
