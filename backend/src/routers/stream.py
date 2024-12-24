from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from typing import Annotated
from fastapi.responses import FileResponse, StreamingResponse
from sqlmodel import Session, select
from db import get_db
from models.music import MusicTrack
from models.video import Video
from models.file import FileModal
import re

stream_router = APIRouter(prefix="/stream", tags=["stream"])

SessionDep = Annotated[Session, Depends(get_db)]


@stream_router.get("/music/{track_id}")
async def stream_music(
    track_id: int,
    request: Request,
    session: SessionDep,
):
    music = session.exec(select(MusicTrack).where(MusicTrack.id == track_id)).first()
    if not music or not music.file:
        raise HTTPException(status_code=404, detail="找不到音樂檔案")

    file_path = Path(music.file.filepath)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="音樂檔案不存在")

    file_size = file_path.stat().st_size
    range_header = request.headers.get("Range")
    if range_header:
        range_match = re.match(r"bytes=(\d+)-(\d+)?", range_header)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
        else:
            start = 0
            end = file_size - 1
    else:
        start = 0
        end = file_size - 1

    async def file_iterator(start: int, end: int):
        chunk_size = 1024 * 1024
        with open(file_path, "rb") as file:
            file.seek(start)
            while start <= end:
                bytes_to_read = min(chunk_size, end - start + 1)
                data = file.read(bytes_to_read)
                if not data:
                    break
                start += len(data)
                yield data

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
    }

    return StreamingResponse(
        file_iterator(start, end),
        media_type=f"audio/{music.file.codec.value}",
        headers=headers,
        status_code=206,
    )


@stream_router.head("/music/{track_id}")
async def head_music(
    track_id: int,
    session: SessionDep,
):
    """處理HEAD請求"""
    music = session.exec(select(MusicTrack).where(MusicTrack.id == track_id)).first()
    if not music or not music.file:
        raise HTTPException(status_code=404, detail="找不到音樂檔案")

    file_path = Path(music.file.filepath)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="音樂檔案不存在")

    file_size = file_path.stat().st_size

    headers = {
        "Content-Length": str(file_size),
        "Accept-Ranges": "bytes",
        "Content-Type": f"audio/{music.file.codec.value}",
    }

    return Response(headers=headers)


@stream_router.get("/video/{video_id}")
async def stream_video(
    video_id: int,
    request: Request,
    session: SessionDep,
):
    """串流影片檔案"""
    video = session.exec(select(Video).where(Video.id == video_id)).first()
    if not video or not video.file:
        raise HTTPException(status_code=404, detail="找不到影片檔案")

    file_path = Path(video.file.filepath)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="影片檔案不存在")

    file_size = file_path.stat().st_size
    range_header = request.headers.get("Range")

    if range_header:
        range_match = re.match(r"bytes=(\d+)-(\d+)?", range_header)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2)) if range_match.group(2) else file_size - 1
        else:
            start = 0
            end = file_size - 1
    else:
        start = 0
        end = file_size - 1

    async def file_iterator(start: int, end: int):
        chunk_size = 1024 * 1024
        with open(file_path, "rb") as file:
            file.seek(start)
            while start <= end:
                bytes_to_read = min(chunk_size, end - start + 1)
                data = file.read(bytes_to_read)
                if not data:
                    break
                start += len(data)
                yield data

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Type": f"video/{video.file.format.lower()}",
    }

    return StreamingResponse(
        file_iterator(start, end),
        headers=headers,
        status_code=206 if range_header else 200,
    )


@stream_router.head("/video/{video_id}")
async def head_video(
    video_id: int,
    session: SessionDep,
):
    """處理 HEAD 請求"""
    video = session.exec(select(Video).where(Video.id == video_id)).first()
    if not video or not video.file:
        raise HTTPException(status_code=404, detail="找不到影片檔案")

    file_path = Path(video.file.filepath)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="影片檔案不存在")

    file_size = file_path.stat().st_size

    headers = {
        "Content-Length": str(file_size),
        "Accept-Ranges": "bytes",
        "Content-Type": f"video/{video.file.format.lower()}",
    }

    return Response(headers=headers)


@stream_router.get("/file/{file_id}")
async def get_file(
    file_id: int,
    session: SessionDep,
):
    """獲取檔案"""
    file = session.exec(select(FileModal).where(FileModal.id == file_id)).first()
    if not file:
        raise HTTPException(status_code=404, detail="找不到檔案")
    file_path = Path(file.filepath)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="檔案不存在")
    return FileResponse(file_path)


@stream_router.get("/video/{video_id}/subtitle/{language}")
async def get_subtitle(
    video_id: int,
    language: str,
):
    """獲取影片字幕"""
    ...


@stream_router.get("/music/{track_id}/lyrics")
async def get_lyrics(
    track_id: int,
):
    """獲取歌詞"""
    ...
