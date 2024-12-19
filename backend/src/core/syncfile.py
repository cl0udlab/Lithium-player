from pathlib import Path
import os
from db import get_db
from core.fileparser import FileParser, FileType
from sqlmodel import Session, select, union
from models import VideoFile, MusicTrackFile, Video, MusicTrack, Album


def sync_music_file(metadata: dict, db: Session):
    """同步音樂檔案到資料庫"""
    musicdata = {
        "title": metadata.get("title"),
        "duration": metadata.get("duration", 0),
        "artist": metadata.get("artist", "Unknown Artist"),
        "album_artist": metadata.get("album_artist"),
        "album": metadata.get("album"),
        "release_year": metadata.get("year"),
        "composer": metadata.get("composer"),
        "genre": metadata.get("genre"),
        "track_number": metadata.get("track_number"),
        "disc_number": metadata.get("disc_number"),
        "cover_art": metadata.get("cover_art"),
    }
    track = MusicTrack(**musicdata)

    track_file = MusicTrackFile(
        filename=Path(metadata.get("file_path")).name,
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
                    release_year=metadata.get("year"),
                )
                db.add(album)
            track.album_ref = album
        db.add(track_file)
        db.commit()

        return track_file

    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to sync music file: {str(e)}")


def sync_dir_file(dir_path: Path) -> list:
    db: Session = get_db()
    if not dir_path.is_dir():
        raise ValueError("Invalid directory path")
    query = union(select(VideoFile.filepath), select(MusicTrackFile.filepath))
    exist_files = db.exec(query).all()
    files = []
    for root, _, files in os.walk(dir_path):
        for file in files:
            file_path = Path(root) / file
            # TODO: Error log
            if file_path in exist_files:
                continue
            try:
                files.append(FileParser().parse_file(file_path))
            except Exception:
                pass
    return files


def sync_one_file(file_path: Path):
    db: Session = next(get_db())
    if not file_path.is_file():
        raise ValueError("Invalid file path")
    query = union(select(VideoFile.filepath), select(MusicTrackFile.filepath))
    exist_files = db.exec(query).all()
    if file_path in exist_files:
        raise ValueError("File already exists")
    try:
        file = FileParser().parse_file(file_path)
    except Exception:
        return
    if file.get("file_type") == FileType.MUSIC:
        sync_music_file(metadata=file, db=db)
    elif file.get("file_type") == FileType.VIDEO:
        video = VideoFile(filepath=file_path)
        video.video = Video(**file)
        db.add(video)
        db.commit()
    return file
