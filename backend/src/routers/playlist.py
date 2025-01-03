from datetime import datetime
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from db import get_db
from auth import get_user
from models import (
    User,
    Playlist,
    PlaylistTrack,
    MusicTrack,
    StreamTrack,
    Track_type,
    MusicTrackFile,
)
from core.logger import logger

playlist_router = APIRouter(prefix="/playlist", tags=["playlist"])

SessionDep = Annotated[Session, Depends(get_db)]


@playlist_router.get("/playlist", response_model=list[Playlist])
async def get_playlists(session: SessionDep, user: User = Depends(get_user)):
    playlists = session.exec(select(Playlist).where(Playlist.user_id == user.id)).all()
    return playlists


class TrackResponse(BaseModel):
    id: int
    title: str
    artist: Optional[str] = None
    file: Optional[MusicTrackFile] = None


class PlaylistTrackResponse(BaseModel):
    id: int
    position: int
    track_type: Track_type
    track: Optional[TrackResponse] = None
    streamtrack: Optional[StreamTrack] = None


class PlaylistResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    user_id: int
    tracks: list[PlaylistTrackResponse]


@playlist_router.get("/playlist/{playlist_id}", response_model=PlaylistResponse)
async def get_playlist(
    playlist_id: int, session: SessionDep, user: User = Depends(get_user)
):
    stmt = (
        select(Playlist)
        .where(Playlist.id == playlist_id, Playlist.user_id == user.id)
        .options(
            selectinload(Playlist.tracks).selectinload(PlaylistTrack.track),
            selectinload(Playlist.tracks).selectinload(PlaylistTrack.streamtrack),
        )
    )

    logger.debug(f"Query: {stmt}")
    playlist = session.exec(stmt).first()
    logger.debug(f"Playlist: {playlist}")

    if not playlist:
        raise HTTPException(status_code=404, detail="找不到播放清單")

    tracks = []
    for track in playlist.tracks:
        if track.track_type == Track_type.track and track.track:
            tracks.append(
                PlaylistTrackResponse(
                    id=track.id,
                    position=track.position,
                    track_type=track.track_type,
                    track=TrackResponse(
                        id=track.track.id,
                        title=track.track.title,
                        artist=track.track.artist,
                        file=track.track.file,
                    ),
                )
            )
        elif track.track_type == Track_type.stream and track.streamtrack:
            tracks.append(
                PlaylistTrackResponse(
                    id=track.id,
                    position=track.position,
                    track_type=track.track_type,
                    streamtrack=track.streamtrack,
                )
            )

    return PlaylistResponse(
        id=playlist.id,
        name=playlist.name,
        description=playlist.description,
        created_at=playlist.created_at,
        updated_at=playlist.updated_at,
        user_id=playlist.user_id,
        tracks=tracks,
    )


class PlaylistInput(BaseModel):
    name: str


@playlist_router.post("/playlist")
async def create_playlist(
    session: SessionDep, req: PlaylistInput, user: User = Depends(get_user)
):
    """
    Create a new playlist
    """
    playlist = Playlist(name=req.name, user_id=user.id)
    session.add(playlist)
    session.commit()
    return playlist


class PlaylistTrackInput(BaseModel):
    track_id: Optional[int] = None
    stream_id: Optional[int] = None


@playlist_router.post("/playlist/{playlist_id}")
async def add_track_to_playlist(
    playlist_id: int,
    input: PlaylistTrackInput,
    session: SessionDep,
    user: User = Depends(get_user),
):
    """新增曲目到播放清單"""
    try:
        # 檢查播放清單是否存在且屬於該用戶
        playlist = session.exec(
            select(Playlist).where(
                Playlist.id == playlist_id, Playlist.user_id == user.id
            )
        ).first()
        if not playlist:
            raise HTTPException(status_code=404, detail="找不到播放清單")
        existing_track = session.exec(
            select(PlaylistTrack).where(
                PlaylistTrack.playlist_id == playlist_id,
                PlaylistTrack.track_id == input.track_id,
            )
        ).first()

        if existing_track:
            raise HTTPException(status_code=400, detail="歌曲已存在於播放清單中")

        # 取得目前位置
        count = (
            session.exec(
                select(func.count("*"))
                .select_from(PlaylistTrack)
                .where(PlaylistTrack.playlist_id == playlist_id)
            ).first()
            or 0
        )

        playlist_track = PlaylistTrack(
            playlist_id=playlist_id,
            track_id=input.track_id,
            streamtrack_id=input.stream_id,
            position=count + 1,
            track_type=Track_type.track if input.track_id else Track_type.stream,
        )

        if input.track_id:
            track = session.exec(
                select(MusicTrack).where(MusicTrack.id == input.track_id)
            ).first()
            if not track:
                raise HTTPException(status_code=404, detail="找不到音樂")
        elif input.stream_id:
            stream = session.exec(
                select(StreamTrack).where(StreamTrack.id == input.stream_id)
            ).first()
            if not stream:
                raise HTTPException(status_code=404, detail="找不到串流")
        else:
            raise HTTPException(
                status_code=400, detail="需要提供 track_id 或 stream_id"
            )

        session.add(playlist_track)
        session.commit()
        return playlist_track

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"新增歌曲到播放清單失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"新增失敗: {str(e)}")


@playlist_router.delete("/playlist/{playlist_id}")
async def delete_playlist(
    playlist_id: int, session: SessionDep, user: User = Depends(get_user)
):
    """刪除播放清單"""
    playlist = session.exec(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == user.id)
    ).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="找不到播放清單")

    session.delete(playlist)
    session.commit()
    return {"message": "播放清單已刪除"}


@playlist_router.delete("/playlist/{playlist_id}/track/{track_position}")
async def remove_track_from_playlist(
    playlist_id: int,
    track_position: int,
    session: SessionDep,
    user: User = Depends(get_user),
):
    """從播放清單中移除歌曲"""
    playlist = session.exec(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == user.id)
    ).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="找不到播放清單")

    track = session.exec(
        select(PlaylistTrack).where(
            PlaylistTrack.playlist_id == playlist_id,
            PlaylistTrack.position == track_position,
        )
    ).first()
    if not track:
        raise HTTPException(status_code=404, detail="找不到歌曲")
    session.exec(
        select(PlaylistTrack).where(
            PlaylistTrack.playlist_id == playlist_id,
            PlaylistTrack.position > track_position,
        )
    ).all().update({"position": PlaylistTrack.position - 1})

    session.delete(track)
    session.commit()
    return {"message": "歌曲已從播放清單中移除"}


class ReorderInput(BaseModel):
    track_positions: list[int]


@playlist_router.put("/playlist/{playlist_id}/reorder")
async def reorder_playlist(
    playlist_id: int,
    input: ReorderInput,
    session: SessionDep,
    user: User = Depends(get_user),
):
    """重新排序播放清單"""
    playlist = session.exec(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.user_id == user.id)
    ).first()
    if not playlist:
        raise HTTPException(status_code=404, detail="找不到播放清單")

    tracks = session.exec(
        select(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist_id)
    ).all()
    if len(tracks) != len(input.track_positions):
        raise HTTPException(status_code=400, detail="位置數量不符")
    position_map = {
        track.position: new_pos for new_pos, track in zip(input.track_positions, tracks)
    }
    for track in tracks:
        track.position = position_map[track.position]

    session.commit()
    return {"message": "播放清單已重新排序"}
