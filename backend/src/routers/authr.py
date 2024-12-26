from typing import Annotated
from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import Session, select
from auth import (
    Token,
    LoginRequest,
    RegisterRequest,
    verify_password,
    decode_token,
    create_tokens,
    create_access_token,
    create_refresh_token,
    get_password_hash,
)
from db import get_db
from models.user import User
from datetime import datetime, timedelta

auth_router = APIRouter(prefix="/auth", tags=["authentication"])
SessionDep = Annotated[Session, Depends(get_db)]


@auth_router.post("/register", response_model=Token)
async def register(register_data: RegisterRequest, session: SessionDep):
    """使用者註冊"""
    user: User = session.exec(
        select(User).where(User.username == register_data.username)
    ).first()
    if user:
        raise HTTPException(status_code=400, detail="Username already registered")
    try:
        user = User(
            username=register_data.username,
            password_hash=get_password_hash(register_data.password),
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return create_tokens(user)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@auth_router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, session: SessionDep):
    """使用者登入"""
    user: User = session.exec(select(User).where(User.username == login_data.username)).first()
    if user is None or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return create_tokens(user)


@auth_router.post("/refresh", response_model=Token)
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
