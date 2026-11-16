from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from auth.auth import is_admin, get_user
from core import subsonic
from db import get_db
from models import StreamTrack, StreamPlatform

subsonic_router = APIRouter(prefix="/subsonic", tags=["subsonic"])
SessionDep = Annotated[Session, Depends(get_db)]


@subsonic_router.get("/connection", dependencies=[Depends(is_admin)])
def connection_status():
    connection = subsonic.load_connection()
    return {"url": connection.url, "username": connection.username} if connection else None


@subsonic_router.put("/connection", dependencies=[Depends(is_admin)])
def connect(connection: subsonic.Connection):
    # Do not replace a working configuration until authentication succeeds.
    try:
        subsonic.call(connection, "ping")
        subsonic.save_connection(connection)
    except subsonic.SubsonicError as exc:
        raise HTTPException(502, str(exc)) from exc
    return {"message": "Subsonic 已連線"}


@subsonic_router.delete("/connection", dependencies=[Depends(is_admin)])
def disconnect():
    subsonic.disconnect()
    return {"message": "已中斷連結；曲目、播放清單與快取仍保留"}


@subsonic_router.post("/sync", dependencies=[Depends(is_admin)])
def sync(session: SessionDep):
    connection = subsonic.load_connection()
    if not connection:
        raise HTTPException(409, "請先設定 Subsonic 連線")
    try:
        songs = subsonic.library(connection)
        existing = {track.url: track for track in session.exec(
            select(StreamTrack).where(StreamTrack.url.startswith("subsonic://"))).all()}
        for song in songs:
            url = subsonic.song_url(connection, song["id"])
            track = existing.get(url) or StreamTrack(
                url=url, title="", artist="", duration=0, platform=StreamPlatform.UNKNOWN)
            track.title = song.get("title") or str(song["id"])
            track.artist = song.get("artist") or "Unknown Artist"
            track.duration = int(song.get("duration") or 0)
            session.add(track)
            session.flush()
            if song.get("coverArt"):
                track.cover_art = f"/subsonic/cover/{track.id}?art={quote(str(song['coverArt']), safe='')}"
            session.add(track)
        session.commit()
    except subsonic.SubsonicError as exc:
        session.rollback()
        raise HTTPException(502, str(exc)) from exc
    return {"total": len(songs)}


@subsonic_router.get("/tracks", dependencies=[Depends(get_user)])
def tracks(session: SessionDep):
    return [{**track.model_dump(), "kind": "stream",
             "cached": subsonic.cache_path(track.url).exists()}
            for track in session.exec(select(StreamTrack).where(
                StreamTrack.url.startswith("subsonic://")).order_by(StreamTrack.title)).all()]


def get_track(session, track_id):
    track = session.get(StreamTrack, track_id)
    if not track or not track.url.startswith("subsonic://"):
        raise HTTPException(404, "找不到 Subsonic 曲目")
    return track


@subsonic_router.post("/cache/{track_id}", dependencies=[Depends(get_user)])
def cache(track_id: int, session: SessionDep):
    track = get_track(session, track_id)
    try:
        subsonic.cached_audio(track.url)
    except subsonic.SubsonicError as exc:
        raise HTTPException(503, str(exc)) from exc
    return {"cached": True}


@subsonic_router.get("/cover/{track_id}")
def cover(track_id: int, art: str, session: SessionDep):
    track = get_track(session, track_id)
    try:
        return FileResponse(subsonic.cover(track.url, art), media_type="image/jpeg")
    except subsonic.SubsonicError as exc:
        raise HTTPException(404, str(exc)) from exc
