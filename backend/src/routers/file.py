from fastapi import APIRouter, UploadFile, File, Depends, HTTPException

router = APIRouter(prefix="/files", tags=["files"])

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),

):
    """上傳檔案並提取metadata"""
    ...

@router.get("/music/{track_id}")
async def get_music_file(
    track_id: int,

):
    """獲取音樂檔案資訊"""
    ...

@router.get("/video/{video_id}")
async def get_video_file(
    video_id: int,

):
    """獲取影片檔案資訊"""
    ...

@router.delete("/{file_id}")
async def delete_file(
    file_id: int,

):
    """刪除檔案"""
    ...