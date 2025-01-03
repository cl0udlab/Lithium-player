from typing import Annotated
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from db import get_db
from models import AnimeSeries

video_router = APIRouter(prefix="/video", tags=["video"])

SessionDep = Annotated[Session, Depends(get_db)]


@video_router.get("/anime", response_model=AnimeSeries)
async def get_anime(session: SessionDep):
    """獲取動畫列表"""
    animes = session.exec(AnimeSeries).all()
    return animes


@video_router.get("/anime/{anime_id}", response_model=AnimeSeries)
async def get_anime_by_id(anime_id: int, session: SessionDep):
    """獲取動畫資訊"""
    stmt = (
        select(AnimeSeries)
        .where(AnimeSeries.id == anime_id)
        .options(selectinload(AnimeSeries.tags), selectinload(AnimeSeries.episodes))
    )
    anime = session.exec(stmt).first()
    return anime
