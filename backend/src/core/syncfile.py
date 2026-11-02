from datetime import datetime
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
    AnimeTagsLink,
    VideoTagsLink,
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
VARIOUS_ARTISTS = "Various Artists"


def sync_text_file(metadata: dict, db: Session):
    """同步文字檔案到資料庫"""
    filem = FileModal(
        filename=metadata.get("filename"),
        filepath=metadata.get("file_path"),
        file_size=metadata.get("file_size"),
        name=metadata.get("title") or metadata.get("filename"),
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


def _sync_anime_series(
    metadata: dict,
    db: Session,
    overwrite: bool = False,
    replaced_images: Optional[list] = None,
) -> Optional[AnimeSeries]:
    if not metadata.get("isanime"):
        return None
    anime = db.exec(
        select(AnimeSeries).where(AnimeSeries.title == metadata["title"])
    ).first()
    is_new = anime is None
    if is_new:
        anime = AnimeSeries(title=metadata["title"], release_date="")
        db.add(anime)

    if is_new or overwrite:
        anime.original_title = metadata.get("original_title")
        anime.description = metadata.get("description")
        anime.season_number = metadata.get("season_number") or 1
        anime.total_episodes = metadata.get("total_episodes")
        anime.release_date = metadata.get("date") or ""
        if not is_new:
            anime.updated_at = datetime.now()

    if (is_new or overwrite or not anime.cover_image) and metadata.get("cover_url"):
        cover = FileParser._try_save_cover_from_url(metadata["cover_url"])
        if cover:
            if replaced_images is not None:
                replaced_images.append(anime.cover_image)
            anime.cover_image = cover
    if not anime.cover_image:
        anime.cover_image = metadata.get("thumbnail")

    tags = metadata.get("tags") or []
    if overwrite and tags:
        anime.tags = []
    for tag in tags:
        anime_tag = db.exec(select(AnimeTag).where(AnimeTag.name == tag)).first()
        anime_tag = anime_tag or AnimeTag(name=tag)
        if anime_tag not in anime.tags:
            anime.tags.append(anime_tag)
    return anime


def _video_title(metadata: dict) -> str:
    parsed_title = metadata.get("title") or metadata.get("filename") or "Unknown Title"
    season_number = metadata.get("season_number")
    if metadata.get("isanime") or season_number in (None, ""):
        return parsed_title
    return f"{parsed_title} - {season_number}"


def _apply_video_metadata(video: Video, video_file: VideoFile, metadata: dict):
    video_file.filename = metadata.get("filename")
    video_file.filepath = metadata.get("file_path")
    video_file.file_size = metadata.get("file_size", 0)
    video_file.codec = metadata.get("codec", "unknown")
    video_file.format = metadata.get("format", "unknown")
    video_file.width = metadata.get("width", 0)
    video_file.height = metadata.get("height", 0)
    video_file.frame_rate = metadata.get("frame_rate", 0)

    video.title = _video_title(metadata)
    video.duration = metadata.get("duration", 0)
    video.description = metadata.get("description")
    video.subtitles = metadata.get("subtitles", [])
    video.audio_tracks = metadata.get("audio_tracks", [])
    video.thumbnail = metadata.get("thumbnail")
    video.episode_number = metadata.get("episode_number", 0)


def sync_video_file(metadata: dict, db: Session):
    """同步影片檔案到資料庫"""
    try:
        logger.debug(f"Syncing video file: {metadata}")
        video_file = VideoFile()
        video = Video()
        _apply_video_metadata(video, video_file, metadata)
        video.file = video_file
        video.series = _sync_anime_series(metadata, db)

        db.add(video)
        db.commit()
        return video

    except Exception as e:
        db.rollback()
        raise Exception(f"同步影片檔案失敗: {str(e)}")


def _image_in_use(image_id: str, db: Session) -> bool:
    for column in (
        Video.thumbnail,
        AnimeSeries.cover_image,
        Album.cover_art,
        MusicTrack.cover_art,
    ):
        if db.exec(select(func.count()).where(column == image_id)).one():
            return True
    return False


def _remove_unused_images(image_ids: list[Optional[str]], db: Session):
    for image_id in {i for i in image_ids if i}:
        if _image_in_use(image_id, db):
            continue
        image_path = FileParser.IMAGES_DIR / Path(image_id).name
        try:
            image_path.unlink(missing_ok=True)
        except OSError as e:
            logger.warning(f"刪除圖片失敗 {image_path}: {str(e)}")


def _delete_video_rows(video: Video, db: Session):
    db.exec(delete(PlayHistory).where(PlayHistory.video_id == video.id))
    db.exec(delete(VideoTagsLink).where(VideoTagsLink.video_id == video.id))
    db.exec(delete(VideoFile).where(VideoFile.video_id == video.id))
    db.delete(video)


def _delete_series_if_empty(series: Optional[AnimeSeries], db: Session) -> bool:
    if series is None:
        return False
    remaining = db.exec(
        select(func.count()).select_from(Video).where(Video.series_id == series.id)
    ).one()
    if remaining:
        return False
    db.exec(delete(AnimeTagsLink).where(AnimeTagsLink.series_id == series.id))
    db.delete(series)
    return True


def delete_video(video_id: int, db: Session) -> bool:
    video = db.get(Video, video_id)
    if not video:
        return False
    series = video.series
    images = [video.thumbnail]
    try:
        _delete_video_rows(video, db)
        db.flush()
        if series and _delete_series_if_empty(series, db):
            images.append(series.cover_image)
        db.commit()
    except Exception as e:
        db.rollback()
        raise Exception(f"刪除影片失敗: {str(e)}")
    _remove_unused_images(images, db)
    return True


def delete_anime(anime_id: int, db: Session) -> bool:
    series = db.get(AnimeSeries, anime_id)
    if not series:
        return False
    images = [series.cover_image]
    try:
        for video in list(series.episodes):
            images.append(video.thumbnail)
            _delete_video_rows(video, db)
        db.flush()
        _delete_series_if_empty(series, db)
        db.commit()
    except Exception as e:
        db.rollback()
        raise Exception(f"刪除動畫失敗: {str(e)}")
    _remove_unused_images(images, db)
    return True


def _refresh_video(
    video: Video,
    db: Session,
    bangumi_id: Optional[int],
    search_title: Optional[str],
    refreshed_series: set[str],
) -> Video:
    if not video.file:
        raise ValueError("影片沒有對應的檔案紀錄")
    file_path = Path(video.file.filepath)
    if not file_path.is_file():
        raise FileNotFoundError(f"檔案已不存在: {file_path}")

    metadata = FileParser.parse_file(file_path, bangumi_id, search_title)
    if "duration" not in metadata:
        raise ValueError(f"無法解析影片: {file_path.name}")
    if bangumi_id and not metadata.get("isanime"):
        _remove_unused_images([metadata.get("thumbnail")], db)
        raise ValueError(f"找不到 Bangumi 條目 {bangumi_id}")

    old_series = video.series
    old_images = [video.thumbnail]

    title = metadata.get("title")
    overwrite = bool(metadata.get("isanime")) and title not in refreshed_series
    series = _sync_anime_series(metadata, db, overwrite, old_images)
    if series:
        refreshed_series.add(series.title)

    _apply_video_metadata(video, video.file, metadata)
    video.series = series
    video.updated_at = datetime.now()
    db.add(video)
    db.flush()
    if old_series is not None and old_series is not series:
        if _delete_series_if_empty(old_series, db):
            old_images.append(old_series.cover_image)
    db.commit()
    _remove_unused_images(old_images, db)
    db.refresh(video)
    return video


def refresh_video(
    video_id: int,
    db: Session,
    bangumi_id: Optional[int] = None,
    search_title: Optional[str] = None,
) -> Optional[Video]:
    video = db.get(Video, video_id)
    if not video:
        return None
    try:
        return _refresh_video(video, db, bangumi_id, search_title, set())
    except Exception:
        db.rollback()
        raise


def refresh_anime(
    anime_id: int,
    db: Session,
    bangumi_id: Optional[int] = None,
    search_title: Optional[str] = None,
) -> Optional[int]:
    series = db.get(AnimeSeries, anime_id)
    if not series:
        return None
    episode_ids = [ep.id for ep in series.episodes]
    refreshed_series: set[str] = set()
    new_series_id = None
    errors = []
    for episode_id in episode_ids:
        video = db.get(Video, episode_id)
        try:
            video = _refresh_video(
                video, db, bangumi_id, search_title, refreshed_series
            )
            new_series_id = new_series_id or video.series_id
        except Exception as e:
            db.rollback()
            logger.error(f"重新刮削影片 {episode_id} 失敗: {str(e)}")
            errors.append(str(e))
    if errors and len(errors) == len(episode_ids):
        raise ValueError(errors[0])
    return new_series_id


def remove_missing_videos(dir_path: Path) -> int:
    db: Session = next(get_db())
    if not dir_path.is_dir():
        raise ValueError("Invalid directory path")
    dir_path = dir_path.resolve()
    if not any(dir_path.iterdir()):
        logger.warning(f"{dir_path} 是空的, 略過檢查遺失的影片")
        return 0
    rows = db.exec(select(VideoFile.filepath, VideoFile.video_id)).all()
    removed = 0
    for filepath, video_id in rows:
        path = _resolve_db_filepath(filepath)
        if path is None or not path.is_relative_to(dir_path) or path.is_file():
            continue
        logger.info(f"檔案已不存在, 從媒體庫移除: {path}")
        if delete_video(video_id, db):
            removed += 1
    return removed


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


def _find_album_in_dir(title: str, directory: Path, db: Session) -> Optional[Album]:
    rows = db.exec(
        select(Album, MusicTrackFile.filepath)
        .join(MusicTrack, MusicTrack.album_id == Album.id)
        .join(MusicTrackFile, MusicTrackFile.track_id == MusicTrack.id)
        .where(Album.title == title)
    ).all()
    for album, filepath in rows:
        path = _resolve_db_filepath(filepath)
        if path is not None and path.parent == directory:
            return album
    return None


def merge_split_albums() -> int:
    db: Session = next(get_db())
    rows = db.exec(
        select(Album.id, Album.title, MusicTrackFile.filepath)
        .join(MusicTrack, MusicTrack.album_id == Album.id)
        .join(MusicTrackFile, MusicTrackFile.track_id == MusicTrack.id)
    ).all()
    groups: dict[tuple[str, Path], set[int]] = {}
    for album_id, title, filepath in rows:
        path = _resolve_db_filepath(filepath)
        if path is not None:
            groups.setdefault((title, path.parent), set()).add(album_id)

    merged_into: dict[int, int] = {}

    def resolve(album_id: int) -> int:
        while album_id in merged_into:
            album_id = merged_into[album_id]
        return album_id

    old_covers = []
    targets = set()
    try:
        for ids in groups.values():
            target_id, *other_ids = sorted({resolve(i) for i in ids})
            if not other_ids:
                continue
            target = db.get(Album, target_id)
            for other_id in other_ids:
                other = db.get(Album, other_id)
                for track in db.exec(
                    select(MusicTrack).where(MusicTrack.album_id == other_id)
                ).all():
                    track.album_id = target_id
                    db.add(track)
                if other.album_artist != target.album_artist:
                    target.album_artist = VARIOUS_ARTISTS
                target.cover_art = target.cover_art or other.cover_art
                target.genre = target.genre or other.genre
                target.release_date = target.release_date or other.release_date
                old_covers.append(other.cover_art)
                db.flush()
                db.delete(other)
                merged_into[other_id] = target_id
                logger.info(f"合併專輯 {other_id} -> {target_id}: {target.title}")
            db.add(target)
            targets.add(target_id)
        db.commit()
    except Exception as e:
        db.rollback()
        raise Exception(f"合併專輯失敗: {str(e)}")

    for album_id in targets:
        sync_album_data(album_id, db)
    _remove_unused_images(old_covers, db)
    return len(merged_into)


def sync_music_file(metadata: dict, db: Session):
    """同步音樂檔案到資料庫"""
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
            album = None
            if metadata.get("file_path"):
                album = _find_album_in_dir(
                    metadata["album"], Path(metadata["file_path"]).resolve().parent, db
                )
            if not album:
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
            elif album.album_artist != album_artist:
                album.album_artist = VARIOUS_ARTISTS
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
