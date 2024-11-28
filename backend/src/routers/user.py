from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/me")
async def get_my_playlists():
    """獲取使用者資訊"""
    ...
