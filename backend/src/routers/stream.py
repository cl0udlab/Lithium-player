from fastapi import APIRouter, Depends, HTTPException, Request, Response

router = APIRouter(prefix="/stream", tags=["stream"])

@router.get("/music/{track_id}")
async def stream_music(
    track_id: int,
    request: Request,
    response: Response,
):
    """串流音樂檔案"""
    ...

@router.get("/video/{video_id}")
async def stream_video(
    video_id: int,
    request: Request,
    response: Response,
):
    """串流影片檔案"""
    ...

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