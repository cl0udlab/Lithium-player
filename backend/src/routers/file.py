from datetime import datetime
from typing import Annotated, List, Optional, Union
from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import literal
from models.music import MusicTrack, Album
from models.video import Video
from models.file import FileModal
from sqlmodel import Session, desc, select, or_
from sqlalchemy.orm import selectinload
from db import get_db
from core.syncfile import sync_one_file, sync_dir_file
from pathlib import Path
from core.setting import load_setting
from PIL import Image
import io
from pydantic import BaseModel


class FilePathRequest(BaseModel):
    file_path: str


class AlbumResponse(BaseModel):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    status: str = "ALIVE"
    title: str
    album_artist: Optional[str] = None
    genre: Optional[str] = None
    year: Optional[int] = None
    cover_art: Optional[str] = None
    description: Optional[str] = None
    tracks: List[MusicTrack] = []

    class Config:
        from_attributes = True
        orm_mode = True


class InfoResponse(BaseModel):
    Musics: list[MusicTrack]
    Albums: list[Album]
    Videos: list[Video]

    class Config:
        from_attributes = True


file_router = APIRouter(prefix="/file", tags=["file"])

# TODO: 之後再加入驗證middleware

SessionDep = Annotated[Session, Depends(get_db)]


@file_router.get("/image")
async def get_image_file(
    image_id=Query(..., description="圖片 ID"),
    image_size: Optional[int] = Query(200, description="圖片大小"),
):
    """獲取圖片檔案"""
    image_path = Path(f"data/images/{image_id}")
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="image not exists")
    image = Image.open(image_path)
    image.thumbnail((image_size, image_size))
    image_io = io.BytesIO()
    image.save(image_io, format="JPEG")
    image_io.seek(0)
    return StreamingResponse(image_io, media_type="image/jpeg")


@file_router.get("/info", response_model=InfoResponse)
async def get_info(session: SessionDep, limit: int = 20):
    """獲取所有檔案資訊"""
    musics = session.exec(
        select(MusicTrack)
        .options(selectinload(MusicTrack.file), selectinload(MusicTrack.album_ref))
        .limit(limit)
        .order_by(desc(MusicTrack.id))
    ).all()

    albums = session.exec(
        select(Album).options(selectinload(Album.tracks)).limit(limit)
    ).all()

    videos = session.exec(
        select(Video)
        .options(
            selectinload(Video.file),
            selectinload(Video.series),
            selectinload(Video.tags),
        )
        .limit(limit)
    ).all()

    return {
        "Musics": [track.model_dump() for track in musics],
        "Albums": [album.model_dump() for album in albums],
        "Videos": [video.model_dump() for video in videos],
    }


@file_router.get("/album", response_model=Union[AlbumResponse, List[AlbumResponse]])
async def get_albums(
    session: SessionDep, album_id: Optional[int] = Query(None, description="專輯 ID")
):
    """獲取專輯檔案"""
    if album_id is not None:
        statement = (
            select(Album)
            .options(selectinload(Album.tracks))
            .where(Album.id == album_id)
        )
        album = session.exec(statement).first()

        if not album:
            raise HTTPException(
                status_code=404, detail=f"id:{album_id} album not found"
            )

        return AlbumResponse.model_validate(album)

    statement = select(Album).options(selectinload(Album.tracks))
    albums = session.exec(statement).all()

    return [AlbumResponse.model_validate(album) for album in albums]


@file_router.get("/music", response_model=Union[MusicTrack, list[MusicTrack]])
async def get_music_file(
    session: SessionDep, track_id: Optional[int] = Query(None, description="音樂 ID")
):
    """獲取音樂檔案"""
    if track_id is not None:
        statement = (
            select(MusicTrack)
            .where(MusicTrack.id == track_id)
            .options(selectinload(MusicTrack.file), selectinload(MusicTrack.album_ref))
        )
        music = session.exec(statement).first()
        if not music:
            raise HTTPException(
                status_code=404, detail=f"id:{track_id} music not found"
            )
        return music

    statement = select(MusicTrack).options(
        selectinload(MusicTrack.file), selectinload(MusicTrack.album_ref)
    )
    return session.exec(statement).all()


@file_router.get("/video", response_model=Union[Video, list[Video]])
async def get_video_file(
    session: SessionDep, video_id: Optional[int] = Query(None, description="影片 ID")
):
    """獲取影片檔案"""
    if video_id is not None:
        statement = (
            select(Video)
            .where(Video.id == video_id)
            .options(
                selectinload(Video.file),
                selectinload(Video.series),
                selectinload(Video.tags),
            )
        )
        video = session.exec(statement).first()
        if not video:
            raise HTTPException(
                status_code=404, detail=f"id:{video_id} video not found"
            )
        return video

    statement = select(Video).options(
        selectinload(Video.file),
        selectinload(Video.series),
        selectinload(Video.tags),
    )
    return session.exec(statement).all()


@file_router.get("/file", response_model=Union[FileModal, List[FileModal]])
async def get_file(
    session: SessionDep, file_id: Optional[int] = Query(None, description="檔案 ID")
):
    """獲取檔案"""
    if file_id is not None:
        statement = select(FileModal).where(FileModal.id == file_id)
        file = session.exec(statement).first()
        if not file:
            raise HTTPException(status_code=404, detail=f"id:{file_id} file not found")
        return file

    statement = select(FileModal)
    return session.exec(statement).all()


@file_router.post("/parse_file")
async def parse_one_file(request: FilePathRequest):
    """解析1個檔案"""
    try:
        data = sync_one_file(Path(request.file_path))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return data


@file_router.post("/scanall")
async def scan_all_files(request: FilePathRequest):
    """掃描所有檔案"""
    if Path(request.file_path):
        sync_dir_file(Path(request.file_path))
    else:
        for dir in load_setting().storages:
            sync_dir_file(dir.path)


@file_router.get("/search")
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


@file_router.delete("/{file_id}")
async def delete_file(file_id: int):
    """刪除檔案"""
    ...
