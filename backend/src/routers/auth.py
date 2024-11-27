from fastapi import APIRouter
from auth import Token, LoginRequest

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    """使用者登入"""
    ...


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """更新 token"""
    ...
