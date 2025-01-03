from pathlib import Path
import os

from sqlalchemy import func
from db import get_db
from core.fileparser import FileParser, FileType
from sqlmodel import Session, select, union
from models import (
    VideoFile,
    MusicTrackFile,
    Video,
    MusicTrack,
    Album,
    FileModal,
    AnimeSeries,
    AnimeTag,
)
from core.logger import logger


def sync_text_file(metadata: dict, db: Session):
    """同步文字檔案到資料庫"""
    filem = FileModal(
        filename=metadata.get("filename"),
        filepath=metadata.get("file_path"),
        file_size=metadata.get("file_size"),
        name=metadata.get("filename"),
        file_format=metadata.get("format"),
        size=metadata.get("file_size"),
        pages=metadata.get("pages"),
        author=metadata.get("author"),
        publisher=metadata.get("publisher"),
    )
    try:
        db.add(filem)
        db.commit()
        return filem
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to sync text file: {str(e)}")


def sync_video_file(metadata: dict, db: Session):
    """同步影片檔案到資料庫"""
    try:
        logger.debug(f"Syncing video file: {metadata}")
        logger.info(f"Syncing video file: {metadata}")
        video_file = VideoFile(
            filename=metadata.get("filename"),
            filepath=metadata.get("file_path"),
            file_size=metadata.get("file_size", 0),
            codec=metadata.get("codec", "unknown"),
            format=metadata.get("format", "unknown"),
            width=metadata.get("width", 0),
            height=metadata.get("height", 0),
            frame_rate=metadata.get("frame_rate", 0),
        )

        anime = None
        if metadata.get("isanime"):
            anime = db.exec(
                select(AnimeSeries).where(AnimeSeries.title == metadata["title"])
            ).first()
            if not anime:
                anime = AnimeSeries(
                    title=metadata["title"],
                    description=metadata.get("description"),
                    season_number=metadata.get("season_number", 1),
                    release_date=metadata.get("date"),
                )
                db.add(anime)
            if metadata.get("tags"):
                for tag in metadata["tags"]:
                    anime_tag = db.exec(
                        select(AnimeTag).where(AnimeTag.name == tag)
                    ).first() or AnimeTag(name=tag)
                    if anime_tag not in anime.tags:
                        anime.tags.append(anime_tag)

        video = Video(
            title=metadata.get("title") or metadata["filename"]
            if metadata.get("isanime")
            else metadata.get("titme") + " - " + metadata.get("season_number", 1),
            duration=metadata.get("duration", 0),
            description=metadata.get("description"),
            subtitles=metadata.get("subtitles", []),
            audio_tracks=metadata.get("audio_tracks", []),
            thumbnail=metadata.get("thumbnail"),
            file=video_file,
            series=anime,
            episode_number=metadata.get("episode_number", 0),
        )

        db.add(video)
        db.commit()
        return video

    except Exception as e:
        db.rollback()
        raise Exception(f"同步影片檔案失敗: {str(e)}")


def sync_album_data(album_id: int, db: Session):
    """更新專輯的資料 專輯數量等..."""
    album = db.exec(select(Album).where(Album.id == album_id)).first()
    if not album:
        raise ValueError("Album not found")

    album.total_tracks = db.exec(
        select(func.count())
        .select_from(MusicTrack)
        .where(MusicTrack.album_id == album_id)
    ).first()

    db.add(album)
    db.commit()
    return album


def sync_music_file(metadata: dict, db: Session):
    """同步音樂檔案到資料庫"""
    track = MusicTrack(
        title=metadata.get("title"),
        duration=metadata.get("duration"),
        artist=metadata.get("artist"),
        album_artist=metadata.get("album_artist"),
        album=metadata.get("album"),
        release_date=metadata.get("date"),
        composer=metadata.get("composer"),
        genre=metadata.get("genre"),
        track_number=metadata.get("track_number"),
        disc_number=metadata.get("disc_number"),
        cover_art=metadata.get("cover_art"),
        vocals=metadata.get("vocals"),
        arrangers=metadata.get("arrangers"),
        mixers=metadata.get("mixers"),
        lyrics=metadata.get("lyrics"),
    )

    track_file = MusicTrackFile(
        filename=metadata.get("filename"),
        filepath=metadata.get("file_path"),
        codec=metadata.get("codec", "unknown"),
        bitrate=metadata.get("bitrate", 0),
        sample_rate=metadata.get("sample_rate", 0),
        file_size=metadata.get("file_size", 0),
        audio_type=metadata.get("audio_type", "unknown"),
        track=track,
    )

    try:
        if metadata.get("album"):
            album = db.exec(
                select(Album).where(
                    Album.title == metadata["album"],
                    Album.album_artist
                    == metadata.get("album_artist", "Unknown Artist"),
                )
            ).first()

            if not album:
                album = Album(
                    title=metadata["album"],
                    album_artist=metadata.get("album_artist", "Unknown Artist"),
                    genre=metadata.get("genre"),
                    release_date=metadata.get("date"),
                    cover_art=metadata.get("cover_art"),
                )
                db.add(album)
            track.album_ref = album
        db.add(track_file)
        db.commit()

        if track.album_id:
            sync_album_data(track.album_id, db)

        return track_file

    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to sync music file: {str(e)}")


def sync_dir_file(dir_path: Path) -> list:
    db: Session = next(get_db())
    if not dir_path.is_dir():
        raise ValueError("Invalid directory path")
    query = union(select(VideoFile.filepath), select(MusicTrackFile.filepath))
    exist_files = db.exec(query).all()
    files = []
    for root, _, files in os.walk(dir_path):
        for file in files:
            file_path = Path(root) / file
            if file_path in exist_files:
                logger.debug(f"File {file_path} already exists")
                continue
            try:
                files.append(FileParser().parse_file(file_path))
            except Exception as e:
                logger.error(f"Error parsing file {file_path} : {str(e)}")
                pass
    for file in files:
        if file.get("file_type") == FileType.MUSIC:
            sync_music_file(metadata=file, db=db)
        elif file.get("file_type") == FileType.VIDEO:
            sync_video_file(metadata=file, db=db)
        elif file.get("file_type") == FileType.TEXT:
            sync_text_file(metadata=file, db=db)
    return files


def sync_one_file(file_path: Path):
    db: Session = next(get_db())
    if not file_path.is_file():
        raise ValueError("Invalid file path")
    file_path = file_path.resolve()
    query = union(select(VideoFile.filepath), select(MusicTrackFile.filepath))
    exist_files = [Path(f[0]).resolve() for f in db.exec(query).all()]
    if file_path in exist_files:
        raise ValueError("File already exists")
    try:
        file = FileParser().parse_file(file_path)
    except Exception as e:
        logger.error(f"Error parsing file {file_path}: {str(e)}")
        return
    if file.get("file_type") == FileType.MUSIC:
        sync_music_file(metadata=file, db=db)
    elif file.get("file_type") == FileType.VIDEO:
        sync_video_file(metadata=file, db=db)
    elif file.get("file_type") == FileType.TEXT:
        sync_text_file(metadata=file, db=db)
    return file
