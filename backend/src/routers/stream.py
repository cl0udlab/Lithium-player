from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from typing import Annotated
from fastapi.responses import FileResponse, StreamingResponse
from sqlmodel import Session, select
from db import get_db
from fastapi.concurrency import run_in_threadpool
from starlette.background import BackgroundTask
from models.music import MusicTrack, StreamTrack
from models.video import Video
from models.file import FileModal
from core.musicstream import (
    get_playable_stream,
    get_stream_lyrics,
    invalidate_playable_stream,
)
from core.musiclyrics import find_lyrics, LyricsServiceError
from core.logger import logger
import asyncio
import httpx
import re
import time

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


PROXY_HEADERS = ("content-type", "content-length", "content-range", "accept-ranges")


async def _open_upstream(url: str, headers: dict[str, str]):
    client = httpx.AsyncClient(
        follow_redirects=True, timeout=httpx.Timeout(15.0, read=None)
    )
    try:
        upstream = await client.send(
            client.build_request("GET", url, headers=headers), stream=True
        )
    except Exception:
        await client.aclose()
        raise
    return client, upstream


def _limit_range(range_header: str | None, chunk_size: int | None) -> str | None:
    if not chunk_size:
        return range_header
    match = re.match(r"bytes=(\d+)-(\d+)?$", range_header or "bytes=0-")
    if not match:
        return range_header
    start = int(match.group(1))
    end = start + chunk_size - 1
    if match.group(2):
        end = min(end, int(match.group(2)))
    return f"bytes={start}-{end}"


@stream_router.get("/stream/{stream_id}")
async def stream_online(
    stream_id: int,
    request: Request,
    session: SessionDep,
):
    track = session.get(StreamTrack, stream_id)
    if not track:
        raise HTTPException(status_code=404, detail="找不到網路音訊")

    range_header = request.headers.get("Range")

    async def connect(refresh: bool):
        if refresh:
            invalidate_playable_stream(track.url)
        playable = await run_in_threadpool(get_playable_stream, track.url)
        wait = playable.available_at - time.time()
        if wait > 0:
            await asyncio.sleep(wait)
        headers = {**playable.headers, "Accept-Encoding": "identity"}
        request_range = _limit_range(range_header, playable.chunk_size)
        if request_range:
            headers["Range"] = request_range
        return await _open_upstream(playable.url, headers)

    try:
        client, upstream = await connect(refresh=False)
        if upstream.status_code in (403, 404, 410):
            await upstream.aclose()
            await client.aclose()
            client, upstream = await connect(refresh=True)
    except Exception as e:
        logger.warning(f"取得網路音訊失敗 {track.url}: {str(e)}")
        raise HTTPException(status_code=502, detail="無法取得網路音訊")

    if upstream.status_code >= 400:
        logger.warning(f"網路音訊來源回應 {upstream.status_code}: {track.url}")
        await upstream.aclose()
        await client.aclose()
        raise HTTPException(status_code=502, detail="無法取得網路音訊")

    async def close():
        await upstream.aclose()
        await client.aclose()

    return StreamingResponse(
        upstream.aiter_raw(),
        status_code=upstream.status_code,
        headers={
            k: v for k, v in upstream.headers.items() if k.lower() in PROXY_HEADERS
        },
        background=BackgroundTask(close),
    )


@stream_router.get("/stream/{stream_id}/lyrics")
async def get_stream_lyrics_api(
    stream_id: int,
    session: SessionDep,
    refresh: bool = False,
):
    track = session.get(StreamTrack, stream_id)
    if not track:
        raise HTTPException(status_code=404, detail="找不到網路音訊")

    if track.lyrics is None or refresh:
        try:
            lyrics = await run_in_threadpool(get_stream_lyrics, track.url)
        except Exception as e:
            logger.warning(f"取得歌詞失敗 {track.url}: {str(e)}")
            raise HTTPException(status_code=502, detail="無法取得歌詞")
        # 空字串代表查過但沒有, 避免每次播放都重新解析
        track.lyrics = lyrics or ""
        session.add(track)
        session.commit()

    return {"lyrics": track.lyrics or None}


@stream_router.get("/file/{file_id}")
async def get_file(
    file_id: int,
    session: SessionDep,
):
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
): ...


@stream_router.get("/music/{track_id}/lyrics")
async def get_lyrics(
    track_id: int,
    session: SessionDep,
    refresh: bool = False,
):
    music = session.get(MusicTrack, track_id)
    if not music:
        raise HTTPException(status_code=404, detail="找不到音樂")

    if music.lyrics is None or refresh:
        try:
            lyrics = await run_in_threadpool(
                find_lyrics,
                music.title,
                music.artist,
                music.album,
                music.duration,
            )
        except LyricsServiceError as e:
            logger.warning(f"歌詞服務暫時無法使用: {str(e)}")
            raise HTTPException(status_code=503, detail="歌詞服務暫時無法使用")
        music.lyrics = lyrics or ""
        session.add(music)
        session.commit()

    return {"lyrics": music.lyrics or None}
