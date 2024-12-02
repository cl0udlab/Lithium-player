from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from fastapi.responses import FileResponse, StreamingResponse
from sqlmodel import Session, select
from db import get_db
from models.music import MusicTrack
from models.video import Video
from core.makehls import create_hls
import os

router = APIRouter(prefix="/stream", tags=["stream"])

SessionDep = Annotated[Session, Depends(get_db)]


@router.get("/music/{track_id}")
async def stream_music(
    track_id: int,
    session: SessionDep,
):
    """串流音樂檔案"""
    music = session.exec(select(MusicTrack).where(MusicTrack.id == track_id)).first()
    if not music or not music.file:
        raise HTTPException(status_code=404, detail="找不到音樂檔案")

    file_path = Path(music.file.filepath)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="音樂檔案不存在")

    async def file_iterator():
        chunk_size = 1024 * 1024
        with open(file_path, "rb") as file:
            while chunk := file.read(chunk_size):
                yield chunk

    return StreamingResponse(file_iterator(), media_type=f"audio/{music.file.codec}")


@router.get("/video/{video_id}")
async def stream_video(
    video_id: int,
    session: SessionDep,
):
    """串流影片檔案"""

    video = session.exec(select(Video).where(Video.id == video_id)).first()
    if not video or not video.file:
        raise HTTPException(status_code=404, detail="找不到影片檔案")
    file_path = Path(video.file.filepath)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="影片檔案不存在")
    file_size = os.path.getsize(file_path)
    size_limit = 100 * 1024 * 1024
    if file_size < size_limit:
        async def file_iterator():
            chunk_size = 1024 * 1024
            with open(file_path, "rb") as file:
                while chunk := file.read(chunk_size):
                    yield chunk
        return StreamingResponse(
            file_iterator(), media_type=f"video/{video.file.format.lower()}"
        )

    playlist_path = create_hls(video.file.filepath, Path("temp"))
    return FileResponse(
        playlist_path,
        media_type="application/vnd.apple.mpegurl",
        filename=f"{video.title}.m3u8",
    )


@router.get("/video/{video_id}/subtitle/{language}")
async def get_subtitle(
    video_id: int,
    language: str,
):
    """獲取影片字幕"""
    ...


@router.get("/music/{track_id}/lyrics")
async def get_lyrics(
    track_id: int,
):
    """獲取歌詞"""
    ...
