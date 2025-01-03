from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from db import get_db
from auth import get_user
from models import User, Playlist, PlaylistTrack, MusicTrack, StreamTrack

playlist_router = APIRouter(prefix="/playlist", tags=["playlist"])

SessionDep = Annotated[Session, Depends(get_db)]


@playlist_router.get("/playlist", response_model=list[Playlist])
async def get_playlists(session: SessionDep, user: User = Depends(get_user)):
    playlists = session.exec(select(Playlist).where(Playlist.user_id == user.id)).all()
    return playlists


@playlist_router.post("/playlist")
async def create_playlist(
    session: SessionDep, name: str, user: User = Depends(get_user)
):
    """
    Create a new playlist
    """
    playlist = Playlist(name=name, user_id=user.id)
    session.add(playlist)
    session.commit()
    return playlist


class PlaylistTrackInput(BaseModel):
    playlist_id: int
    track_id: Optional[int]
    stream_id: Optional[int]


@playlist_router.post("/playlist/{playlist_id}/")
async def add_track_to_playlist(
    session: SessionDep, input: PlaylistTrackInput, user: User = Depends(get_user)
):
    """新增曲目到播放清單"""
    try:
        playlist = session.exec(
            select(Playlist).where(
                Playlist.id == input.playlist_id, Playlist.user_id == user.id
            )
        ).first()
        if not playlist:
            raise HTTPException(status_code=404, detail="找不到播放清單")

        position = session.exec(
            select(PlaylistTrack).where(PlaylistTrack.playlist_id == input.playlist_id)
        ).count()

        if input.track_id:
            track = session.exec(
                select(MusicTrack).where(MusicTrack.id == input.track_id)
            ).first()
            if not track:
                raise HTTPException(status_code=404, detail="找不到音樂")
            playlist_track = PlaylistTrack(
                playlist_id=input.playlist_id,
                track_id=input.track_id,
                position=position + 1,
            )
        elif input.stream_id:
            stream = session.exec(
                select(StreamTrack).where(StreamTrack.id == input.stream_id)
            ).first()
            if not stream:
                raise HTTPException(status_code=404, detail="找不到串流")
            playlist_track = PlaylistTrack(
                playlist_id=input.playlist_id,
                stream_id=input.stream_id,
                position=position + 1,
            )
        else:
            raise HTTPException(
                status_code=400, detail="需要提供 track_id 或 stream_id"
            )

        playlist.tracks.append(playlist_track)
        session.commit()
        return playlist

    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
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
