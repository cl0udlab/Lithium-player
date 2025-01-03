from typing import Annotated, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from db import get_db
from models import AnimeSeries, VideoFile
from fastapi import HTTPException

video_router = APIRouter(prefix="/video", tags=["video"])

SessionDep = Annotated[Session, Depends(get_db)]


class TagResponse(BaseModel):
    id: Optional[int]
    name: str
    description: Optional[str]


class EpisodeResponse(BaseModel):
    id: Optional[int]
    episode_number: Optional[int]
    title: Optional[str]
    file: Optional[VideoFile]
    description: Optional[str]
    subtitles: list[str]
    audio_tracks: list[str]
    thumbnail: Optional[str]
    series_id: Optional[int]
    episode_number: Optional[int]


class AnimeResponse(BaseModel):
    id: Optional[int]
    title: str
    original_title: Optional[str]
    release_date: str
    author: Optional[str]
    studio: Optional[str]
    description: Optional[str]
    season_number: Optional[int]
    total_episodes: Optional[int]
    cover_image: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    tags: list[TagResponse] = []
    episodes: list[EpisodeResponse] = []

    class Config:
        from_attributes = True


@video_router.get("/anime", response_model=list[AnimeSeries])
async def get_anime(session: SessionDep):
    """獲取動畫列表"""
    statement = select(AnimeSeries)
    animes = session.exec(statement).all()
    return animes


@video_router.get("/anime/{anime_id}", response_model=AnimeResponse)
async def get_anime_by_id(anime_id: int, session: SessionDep):
    """獲取動畫資訊"""
    stmt = (
        select(AnimeSeries)
        .where(AnimeSeries.id == anime_id)
        .options(selectinload(AnimeSeries.tags), selectinload(AnimeSeries.episodes))
    )

    result = session.exec(stmt).first()

    tags = [
        TagResponse(id=tag.id, name=tag.name, description=tag.description)
        for tag in result.tags
    ]

    # 手動轉換 Video 到 EpisodeResponse
    episodes = [
        EpisodeResponse(
            id=ep.id,
            episode_number=ep.episode_number,
            title=ep.title,
            file=ep.file,
            description=ep.description,
            subtitles=ep.subtitles,
            audio_tracks=ep.audio_tracks,
            thumbnail=ep.thumbnail,
            series_id=ep.series_id,
        )
        for ep in result.episodes
    ]

    if not result:
        raise HTTPException(status_code=404, detail=f"找不到 ID 為 {anime_id} 的動畫")
    return AnimeResponse(
        id=result.id,
        title=result.title,
        original_title=result.original_title,
        release_date=result.release_date,
        author=result.author,
        studio=result.studio,
        description=result.description,
        season_number=result.season_number,
        total_episodes=result.total_episodes,
        cover_image=result.cover_image,
        created_at=str(result.created_at) if result.created_at else None,
        updated_at=str(result.updated_at) if result.updated_at else None,
        tags=tags,
        episodes=episodes,
    )
