from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from auth.auth import is_admin, get_user
from core import subsonic
from db import get_db
from models import StreamTrack, StreamPlatform, Album, SubsonicSong, MusicTrack
from sqlalchemy import func

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
        metadata = {item.track_id: item for item in session.exec(select(SubsonicSong)).all()}
        albums = {(item.source, item.remote_album_id): item.album_id for item in metadata.values()}
        for song in songs:
            url = subsonic.song_url(connection, song["id"])
            track = existing.get(url) or StreamTrack(
                url=url, title="", artist="", duration=0, platform=StreamPlatform.UNKNOWN)
            track.title = song.get("title") or str(song["id"])
            track.artist = song.get("artist") or "Unknown Artist"
            track.duration = int(song.get("duration") or 0)
            session.add(track)
            session.flush()
            album_key = str(song.get("albumId") or f"{song.get('album', '')}:{song.get('artist', '')}")
            key = (connection.identity, album_key)
            album = session.get(Album, albums[key]) if albums.get(key) else None
            if album is None:
                album = Album(title=song.get("album") or "未分類專輯",
                              album_artist=song.get("albumArtist") or track.artist)
                session.add(album)
                session.flush()
                albums[key] = album.id
            item = metadata.get(track.id) or SubsonicSong(
                track_id=track.id, source=connection.identity, remote_album_id=album_key)
            item.album_id = album.id
            item.album = song.get("album") or album.title
            item.track_number = int(song.get("track") or 0)
            item.disc_number = int(song.get("discNumber") or 0)
            album.title = item.album
            album.album_artist = song.get("albumArtist") or album.album_artist
            album.genre = song.get("genre") or album.genre
            album.release_date = str(song["year"]) if song.get("year") else album.release_date
            if song.get("coverArt"):
                track.cover_art = f"/subsonic/art/{connection.identity}?id={quote(str(song['coverArt']), safe='')}"
                album.cover_art = track.cover_art
            session.add(item)
            session.add(album)
            session.add(track)
        for album_id in set(albums.values()):
            if album_id:
                album = session.get(Album, album_id)
                album.total_tracks = len(session.exec(select(SubsonicSong).where(SubsonicSong.album_id == album_id)).all())
                album.total_tracks += session.exec(select(func.count()).select_from(MusicTrack)
                                                   .where(MusicTrack.album_id == album_id)).one()
                session.add(album)
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
        return image_response(track.url, art)
    except subsonic.SubsonicError as exc:
        raise HTTPException(404, str(exc)) from exc


def image_response(url, art):
    try:
        return FileResponse(subsonic.cover(url, art), media_type="image/jpeg",
                            headers={"Cache-Control": "public, max-age=86400"})
    except subsonic.SubsonicError as exc:
        raise HTTPException(503, str(exc), headers={"Retry-After": "30", "Cache-Control": "max-age=30"}) from exc


@subsonic_router.get("/art/{source}")
def art(source: str, id: str):
    return image_response(f"subsonic://{source}/", id)
