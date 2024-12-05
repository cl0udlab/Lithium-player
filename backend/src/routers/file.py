from typing import Annotated, Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy import literal
from models.music import MusicTrack, Album
from models.video import Video
from sqlmodel import Session, select, or_
from sqlalchemy.orm import selectinload
from db import get_db
from core.syncfile import scan_one_file, scan_dir_file
from pathlib import Path

router = APIRouter(prefix="/file", tags=["file"])

# TODO: 之後再加入驗證middleware

SessionDep = Annotated[Session, Depends(get_db)]


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上傳檔案並提取metadata"""
    ...


@router.get("/music/{track_id}", response_model=MusicTrack)
async def get_music_file(track_id: int, session: SessionDep):
    """獲取音樂檔案資訊"""
    statement = (
        select(MusicTrack)
        .where(MusicTrack.id == track_id)
        .options(selectinload(MusicTrack.file), selectinload(MusicTrack.album_ref))
    )
    music = session.exec(statement).first()
    if not music:
        raise HTTPException(status_code=404, detail=f"id:{track_id} music not found")
    return music


@router.get("/video/{video_id}")
async def get_video_file(video_id: int, session: SessionDep):
    """獲取影片檔案資訊"""
    statement = (
        select(Video)
        .where(Video.id == video_id)
        .options(
            selectinload(Video.file),
            selectinload(Video.series),
            selectinload(Video.tags),
        )
    )
    music = session.exec(statement).first()
    if not music:
        raise HTTPException(status_code=404, detail=f"id:{video_id} video not found")
    return music


@router.post("/parse_file")
async def parse_one_file(file_path: str):
    """解析1個檔案"""
    scan_one_file(Path(file_path))


@router.post("/scanall")
async def scan_all_files(dir_path: Optional[str] = None):
    """掃描所有檔案"""
    if dir_path:
        scan_dir_file(Path(dir_path))
    else:
        dir = Path("/data")  # TODO: 待改從資料庫抓
        scan_dir_file(dir)


@router.get("/search")
async def search_files(name: str, session: SessionDep):
    """搜尋"""
    videos = select(
        Video.title, Video.description, literal("video").label("type")
    ).where(or_(Video.title.ilike(f"%{name}%"), Video.description.ilike(f"%{name}%")))

    musics = select(
        MusicTrack.title,
        MusicTrack.artist,
        MusicTrack.album,
        literal("music").label("type"),
    ).where(
        or_(
            MusicTrack.title.ilike(f"%{name}%"),
            MusicTrack.artist.ilike(f"%{name}%"),
            MusicTrack.album.ilike(f"%{name}%"),
        )
    )

    albums = select(
        Album.title, Album.album_artist, literal("album").label("type")
    ).where(
        or_(
            Album.title.ilike(f"%{name}%"),
            Album.album_artist.ilike(f"%{name}%"),
        )
    )

    videos = session.exec(videos).all()
    musics = session.exec(musics).all()
    albums = session.exec(albums).all()
    return [
        *[{"id": v.id, "title": v.title, "type": "video"} for v in videos],
        *[{"id": m.id, "title": m.title, "type": "music"} for m in musics],
        *[{"id": a.id, "title": a.title, "type": "album"} for a in albums],
    ]


@router.delete("/{file_id}")
async def delete_file(file_id: int):
    """刪除檔案"""
    ...
