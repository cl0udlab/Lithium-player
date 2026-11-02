from pathlib import Path
from typing import Callable, Optional
import os

from sqlalchemy import delete, func
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
    PlayHistory,
    PlaylistTrack,
    UserLikes,
    UserDislikes,
)
from core.logger import logger


def _resolve_db_filepath(row_value) -> Path | None:
    value = row_value
    if hasattr(row_value, "_mapping"):
        mapping_values = list(row_value._mapping.values())
        value = mapping_values[0] if mapping_values else None
    elif isinstance(row_value, (tuple, list)):
        value = row_value[0] if row_value else None

    if not isinstance(value, (str, os.PathLike)):
        return None

    try:
        return Path(value).resolve()
    except (TypeError, ValueError):
        return None


UNKNOWN_ARTIST = "Unknown Artist"


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

        parsed_title = (
            metadata.get("title") or metadata.get("filename") or "Unknown Title"
        )
        if metadata.get("isanime"):
            video_title = parsed_title
        else:
            season_number = metadata.get("season_number")
            if season_number in (None, ""):
                video_title = parsed_title
            else:
                video_title = f"{parsed_title} - {season_number}"

        video = Video(
            title=video_title,
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
    # 沒有標籤的檔案 (例如 wav) 這些欄位會是 None, 但資料庫是 NOT NULL
    artist = metadata.get("artist") or UNKNOWN_ARTIST
    album_artist = metadata.get("album_artist") or artist
    track = MusicTrack(
        title=metadata.get("title") or metadata.get("filename") or "Unknown Title",
        duration=metadata.get("duration") or 0,
        artist=artist,
        album_artist=album_artist,
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
                    Album.album_artist == album_artist,
                )
            ).first()

            if not album:
                album = Album(
                    title=metadata["album"],
                    album_artist=album_artist,
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


def remove_missing_music(dir_path: Path) -> int:
    db: Session = next(get_db())
    if not dir_path.is_dir():
        raise ValueError("Invalid directory path")
    dir_path = dir_path.resolve()
    rows = db.exec(
        select(MusicTrackFile.filepath, MusicTrack.id, MusicTrack.album_id).join(
            MusicTrack, MusicTrack.id == MusicTrackFile.track_id
        )
    ).all()
    in_dir = []
    for filepath, track_id, album_id in rows:
        path = _resolve_db_filepath(filepath)
        if path is not None and path.is_relative_to(dir_path):
            in_dir.append((path, track_id, album_id))
    if not in_dir:
        return 0

    if not any(dir_path.iterdir()):
        logger.warning(f"{dir_path} 是空的, 略過檢查遺失的音樂")
        return 0

    missing = [(path, tid, aid) for path, tid, aid in in_dir if not path.is_file()]
    if not missing:
        return 0
    track_ids = [tid for _, tid, _ in missing]
    album_ids = {aid for _, _, aid in missing if aid is not None}
    for path, _, _ in missing:
        logger.info(f"檔案已不存在, 從媒體庫移除: {path}")
    try:
        for model in (PlayHistory, PlaylistTrack, UserLikes, UserDislikes):
            db.exec(delete(model).where(model.track_id.in_(track_ids)))
        db.exec(delete(MusicTrackFile).where(MusicTrackFile.track_id.in_(track_ids)))
        db.exec(delete(MusicTrack).where(MusicTrack.id.in_(track_ids)))
        db.commit()
        for album_id in album_ids:
            album = sync_album_data(album_id, db)
            if not album.total_tracks:
                db.delete(album)
                db.commit()
    except Exception as e:
        db.rollback()
        raise Exception(f"移除遺失的音樂失敗: {str(e)}")
    return len(missing)


def sync_dir_file(
    dir_path: Path,
    on_progress: Optional[Callable[[int, int, Path], None]] = None,
) -> list:
    """掃描資料夾, 每處理完一個檔案呼叫 on_progress(已處理, 總數, 檔案)"""
    db: Session = next(get_db())
    if not dir_path.is_dir():
        raise ValueError("Invalid directory path")
    query = union(select(VideoFile.filepath), select(MusicTrackFile.filepath))
    exist_files = {
        path
        for row in db.exec(query).all()
        for path in [_resolve_db_filepath(row)]
        if path is not None
    }
    new_files = []
    for root, _, file_names in os.walk(dir_path):
        for file_name in file_names:
            file_path = (Path(root) / file_name).resolve()
            if file_path in exist_files:
                logger.debug(f"File {file_path} already exists")
                continue
            new_files.append(file_path)

    # 解析完一個就寫入一個, 掃描途中新歌就會出現在媒體庫
    parsed_files = []
    for index, file_path in enumerate(new_files, 1):
        try:
            file = FileParser().parse_file(file_path)
            if file:
                if file.get("file_type") == FileType.MUSIC:
                    sync_music_file(metadata=file, db=db)
                elif file.get("file_type") == FileType.VIDEO:
                    sync_video_file(metadata=file, db=db)
                elif file.get("file_type") == FileType.TEXT:
                    sync_text_file(metadata=file, db=db)
                parsed_files.append(file)
        except ValueError as e:
            logger.debug(f"Skipping unsupported file {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error syncing file {file_path} : {str(e)}")
        if on_progress:
            on_progress(index, len(new_files), file_path)
    return parsed_files


def sync_one_file(file_path: Path):
    db: Session = next(get_db())
    if not file_path.is_file():
        raise ValueError("Invalid file path")
    file_path = file_path.resolve()
    query = union(select(VideoFile.filepath), select(MusicTrackFile.filepath))
    exist_files = [
        path
        for row in db.exec(query).all()
        for path in [_resolve_db_filepath(row)]
        if path is not None
    ]
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
