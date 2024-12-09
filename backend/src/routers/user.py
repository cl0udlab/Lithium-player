from fastapi import APIRouter, Depends, HTTPException

user_router = APIRouter(prefix="/user", tags=["user"])


@user_router.get("/me")
async def get_my_playlists():
    """獲取使用者資訊"""
    ...
