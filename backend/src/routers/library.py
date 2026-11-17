from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, literal, union_all
from sqlmodel import Session, select, or_
from db import get_db
from models import MusicTrack, StreamTrack, Album, SubsonicSong
from core import subsonic

library_router = APIRouter(prefix="/library", tags=["library"])
SessionDep = Annotated[Session, Depends(get_db)]


def track_query():
    local = select(
        MusicTrack.id, MusicTrack.title, MusicTrack.artist, MusicTrack.album,
        MusicTrack.cover_art, MusicTrack.duration, literal("music").label("kind"),
        literal(None).label("url"), MusicTrack.album_id, MusicTrack.track_number,
        MusicTrack.disc_number)
    remote = select(
        StreamTrack.id, StreamTrack.title, StreamTrack.artist, SubsonicSong.album,
        StreamTrack.cover_art, StreamTrack.duration, literal("stream").label("kind"),
        StreamTrack.url, SubsonicSong.album_id, SubsonicSong.track_number,
        SubsonicSong.disc_number).outerjoin(SubsonicSong, StreamTrack.id == SubsonicSong.track_id).where(
            StreamTrack.url.startswith("subsonic://"))
    return union_all(local, remote).subquery()


@library_router.get("/tracks")
def tracks(session: SessionDep, page: int = Query(1, ge=1),
           size: int = Query(50, ge=1, le=100), q: str = "", cached: bool = False):
    collection = track_query()
    stmt = select(collection)
    if q.strip():
        term = f"%{q.strip()}%"
        stmt = stmt.where(or_(collection.c.title.ilike(term), collection.c.artist.ilike(term),
                              collection.c.album.ilike(term)))
    if cached:
        urls = session.exec(select(StreamTrack.url).where(StreamTrack.url.startswith("subsonic://"))).all()
        stmt = stmt.where(collection.c.url.in_([url for url in urls if subsonic.cache_path(url).exists()]))
    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()
    rows = session.execute(stmt.order_by(collection.c.title, collection.c.kind, collection.c.id)
                           .offset((page - 1) * size).limit(size)).mappings().all()
    return {"items": [{**row, "lyrics": None, "platform": "unknown",
                       "cached": bool(row["url"] and subsonic.cache_path(row["url"]).exists())}
                      for row in rows], "total": total, "page": page, "size": size}


@library_router.get("/albums")
def albums(session: SessionDep, page: int = Query(1, ge=1),
           size: int = Query(24, ge=1, le=100), q: str = ""):
    stmt = select(Album)
    if q.strip():
        term = f"%{q.strip()}%"
        stmt = stmt.where(or_(Album.title.ilike(term), Album.album_artist.ilike(term)))
    total = session.exec(select(func.count()).select_from(stmt.subquery())).one()
    items = session.exec(stmt.order_by(Album.title, Album.id).offset((page - 1) * size).limit(size)).all()
    return {"items": [album.model_dump() for album in items], "total": total, "page": page, "size": size}


@library_router.get("/albums/{album_id}")
def album(album_id: int, session: SessionDep):
    album = session.get(Album, album_id)
    if not album:
        raise HTTPException(404, "找不到專輯")
    collection = track_query()
    rows = session.execute(select(collection).where(collection.c.album_id == album_id).order_by(
        collection.c.disc_number, collection.c.track_number, collection.c.id)).mappings().all()
    return {**album.model_dump(), "tracks": [{**row, "lyrics": None, "platform": "unknown"} for row in rows]}
