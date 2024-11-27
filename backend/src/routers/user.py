from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/user", tags=["user"])

@router.post("/register")
async def register_user(
    username: str,
    password: str,
):
    """註冊新使用者"""
    ...

@router.post("/login")
async def login(
    username: str,
    password: str,
):
    """使用者登入"""
    ...

@router.get("/me")
async def get_my_playlists(
):
    """獲取使用者資訊"""
    ...
