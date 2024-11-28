from fastapi import APIRouter, HTTPException, status
from sqlmodel import select
from auth import (
    Token,
    LoginRequest,
    verify_password,
    decode_token,
    create_tokens,
    create_access_token,
    create_refresh_token,
)
from models.user import User
from db import get_db
from datetime import datetime, timedelta

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    """使用者登入"""
    with get_db() as db:
        user: User = db.exec(select(User).where(User.username == login_data.username))
        if user is None or not verify_password(login_data.password, user.password_hash):
            raise HTTPException(status_code=400, detail="Invalid credentials")
    return create_tokens(user.id)


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """更新 token"""
    try:
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="not a refresh token"
            )

        userid = payload.get("userid")
        if not userid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token"
            )

        exp = payload.get("exp")
        remaining_time = datetime.fromtimestamp(exp) - datetime.now()
        renewal_threshold = timedelta(days=2)

        response = {
            "access_token": create_access_token(userid),
            "refresh_token": None,
            "token_type": "bearer",
        }

        if remaining_time < renewal_threshold:
            response["refresh_token"] = create_refresh_token(userid)

        return response
    except Exception as _:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="cannot verify reflash token",
        )
