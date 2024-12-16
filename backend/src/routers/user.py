from typing import Annotated
from fastapi import APIRouter, Depends
from sqlmodel import Session
from pydantic import BaseModel

from db import get_db
from auth import get_user
from models import User

user_router = APIRouter(prefix="/user", tags=["user"])

SessionDep = Annotated[Session, Depends(get_db)]


class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        from_attributes = True


@user_router.get("/me", response_model=UserResponse)
async def get_my_playlists(user: User = Depends(get_user)):
    """獲取使用者資訊"""
    return user
