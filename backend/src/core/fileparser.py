from datetime import datetime
from pathlib import Path
from typing import Optional, Union
from tinytag import TinyTag
import av
from enum import Enum
from uuid import uuid4
import ebooklib
from ebooklib import epub
from mobi import Mobi
from PyPDF2 import PdfReader
from core.logger import logger
from core.musiclyrics import get_lyrics
from core.musicparser import (
    search_track,
    search_album,
    parse_album_info,
    parse_track_info,
)
from core.filenameparse import parse_filename
from core.animeparser import get_from_Bangumi, get_Bangumi_subject
from core.movieparser import TMDBApi
from core.setting import load_setting
import requests


class FileType(str, Enum):
    MUSIC = "music"
    VIDEO = "video"
    TEXT = "text"
    IMAGE = "image"
    UNKNOWN = "unknown"


class FileParser:
    SUPPORT_MUSIC = {".mp3", ".flac", ".aac", ".ogg", ".opus", ".wav"}
    SUPPORT_VIDEO = {".mp4", ".mkv", ".webm", ".avi", ".flv", ".mov", ".wmv"}
    SUPPORT_TEXT = {".txt", ".pdf", ".epub", ".mobi"}
    SUPPORT_IMAGE = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    IMAGES_DIR = Path("data/images")

    @classmethod
    def save_cover_art(cls, image_data: bytes) -> str:
        cls.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        image_id = str(uuid4())
        image_path = cls.IMAGES_DIR / f"{image_id}.jpg"
        with open(image_path, "wb") as f:
            f.write(image_data)
        return image_id + ".jpg"

    @classmethod
    def save_cover_art_from_url(cls, image_url: str) -> str:
        r = requests.get(image_url, timeout=10)
        r.raise_for_status()
        image_data = r.content
        cls.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        image_id = str(uuid4())
        image_path = cls.IMAGES_DIR / f"{image_id}.jpg"
        with open(image_path, "wb") as f:
            f.write(image_data)
        return image_id + ".jpg"

    @staticmethod
    def get_file_type(file_path: Union[str, Path]) -> FileType:
        file_path = Path(file_path)
        extension = file_path.suffix.lower()

        if extension in FileParser.SUPPORT_MUSIC:
            return FileType.MUSIC
        elif extension in FileParser.SUPPORT_VIDEO:
            return FileType.VIDEO
        elif extension in FileParser.SUPPORT_TEXT:
            return FileType.TEXT
        else:
            raise ValueError(f"Unsupported file type: {extension}")

    @staticmethod
    def parse_file(
        file_path: Union[str, Path],
        bangumi_id: Optional[int] = None,
        search_title: Optional[str] = None,
    ) -> dict:
        """get file metadata"""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_type = FileParser.get_file_type(file_path)
        file_stat = file_path.stat()

        base_info = {
            "filename": file_path.name,
            "file_size": file_stat.st_size,
            "file_path": str(file_path),
            "file_type": file_type,
            "created_at": datetime.fromtimestamp(file_stat.st_ctime),
            "updated_at": datetime.fromtimestamp(file_stat.st_mtime),
        }

        if file_type == FileType.MUSIC:
            return {**base_info, **FileParser._parse_music(file_path)}
        elif file_type == FileType.VIDEO:
            return {
                **base_info,
                **FileParser._parse_video(file_path, bangumi_id, search_title),
            }
        elif file_type == FileType.TEXT:
            return {**base_info, **FileParser._parse_text(file_path)}
        else:
            return base_info

    @staticmethod
    def _epub_meta(book: epub.EpubBook, name: str) -> Optional[str]:
        values = book.get_metadata("DC", name)
        return values[0][0] if values else None

    @staticmethod
    def _mobi_text(value) -> Optional[str]:
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        return value

    @staticmethod
    def _parse_text(file_path: Path) -> dict:
        file_format = file_path.suffix.lower().lstrip(".")

        result = {"format": file_format}
        try:
            if file_format == "epub":
                book = epub.read_epub(str(file_path), options={"ignore_ncx": True})
                result.update(
                    title=FileParser._epub_meta(book, "title"),
                    pages=len(list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))),
                    author=FileParser._epub_meta(book, "creator"),
                    publisher=FileParser._epub_meta(book, "publisher"),
                )
            elif file_format == "mobi":
                book = Mobi(str(file_path))
                book.parse()
                exth = book.config.get("exth", {}).get("records", {})
                result.update(
                    title=FileParser._mobi_text(book.title()),
                    author=FileParser._mobi_text(exth.get(100)),
                    publisher=FileParser._mobi_text(exth.get(101)),
                )
            elif file_format == "pdf":
                reader = PdfReader(file_path)
                metadata = reader.metadata or {}
                result.update(
                    title=metadata.get("/Title"),
                    pages=len(reader.pages),
                    author=metadata.get("/Author"),
                    publisher=metadata.get("/Producer"),
                )
        except Exception as e:
            logger.error(f"Error parsing text file {file_path.name}: {e}")
        return result

    @staticmethod
    def _parse_music(file_path: Path) -> dict:
        try:
            tag = TinyTag.get(file_path, image=True)
            cover_art = tag.images.any
            cover_art_id = None
            online_track = parse_track_info(search_track(tag.title, tag.artist))
            if cover_art and cover_art.data:
                cover_art_id = FileParser.save_cover_art(cover_art.data)
            elif online_track and online_track.cover_art:
                try:
                    cover_art_id = FileParser.save_cover_art_from_url(
                        online_track.cover_art
                    )
                except requests.exceptions.RequestException as e:
                    logger.warning(f"下載線上封面失敗，略過 cover_art: {str(e)}")

            lyrics = get_lyrics(tag.album, tag.artist, tag.title, tag.duration)

            # TODO: 沒有時間修 以後再重構
            return {
                # 原本是 (tag.title or online.title) if online_track else stem,
                # 沒查到線上資料時連有標題標籤的檔案都會變成檔名
                "title": tag.title
                or (online_track.title if online_track else None)
                or file_path.stem,
                "duration": int(tag.duration or 0),
                "bitrate": tag.bitrate or 0,
                "sample_rate": tag.samplerate or 0,
                "artist": tag.artist or (online_track.artist if online_track else None),
                "album": tag.album,
                "album_artist": (
                    tag.albumartist
                    or tag.artist
                    or (online_track.artist if online_track else None)
                ),
                "composer": tag.composer,
                "vocals": [v.name for v in online_track.vocals] if online_track else [],
                "arrangers": online_track.arrangers if online_track else [],
                "mixers": online_track.mixers if online_track else [],
                "genre": tag.genre,
                "date": tag.year
                or (online_track.first_release_date if online_track else None),
                "track_number": tag.track,
                "disc_number": tag.disc,
                "audio_type": "stereo" if (tag.channels or 0) > 1 else "mono",
                "codec": FileParser._get_audio_codec(file_path.suffix),
                "cover_art": cover_art_id,
                "lyrics": lyrics,
                "online_id": online_track.id if online_track else None,
            }
        except Exception as e:
            logger.error(f"Error parsing music file: {e}")
            return {}

    @staticmethod
    def _parse_video(
        file_path: Path,
        bangumi_id: Optional[int] = None,
        search_title: Optional[str] = None,
    ) -> dict:
        """bangumi_id / search_title 用於手動刮削, 沒給就從檔名判斷"""
        try:
            logger.info(f"Parsing video file: {file_path}")
            file_path_str = str(file_path.resolve())
            container = av.open(str(file_path_str))
            video_stream: av.VideoStream = next(
                s for s in container.streams if s.type == "video"
            )
            image_id = None
            title = file_path.stem
            description = ""
            season_number = ""
            date = ""
            episode_number = 1
            tags = []
            original_title = None
            total_episodes = None
            cover_url = None
            anime_success = False
            movie_success = False
            parse_file = parse_filename(file_path.stem)
            logger.info(
                f"Parse file name status: {'failed' if parse_file.parse_failed else 'success'}"
            )
            if not search_title and not parse_file.parse_failed:
                search_title = (
                    parse_file.name_zh or parse_file.name_jp or parse_file.name_en
                )

            bangumi_info = None
            if bangumi_id:
                logger.info(f"Getting info from bangumi subject {bangumi_id}")
                bangumi_info = get_Bangumi_subject(bangumi_id)
            elif search_title:
                logger.info("Getting info from bangumi")
                bangumi_info = get_from_Bangumi(search_title)

            if bangumi_info:
                logger.debug(f"Bangumi info: {bangumi_info}")
                logger.info("success getting info from bangumi")

                cover_url = bangumi_info.images.large if bangumi_info.images else None
                title = bangumi_info.name_cn or bangumi_info.name
                original_title = bangumi_info.name
                description = bangumi_info.summary
                season_number = parse_file.season
                date = bangumi_info.date or ""
                tags = [tag.name for tag in bangumi_info.tags]
                episode_number = parse_file.episode or 1
                total_episodes = bangumi_info.total_episodes or bangumi_info.eps
                anime_success = True
            elif search_title and not bangumi_id:
                logger.info("Getting info from TMDB")
                apikey = load_setting().tmd_api_key
                if apikey == "":
                    logger.error("TMDB API key not set")
                else:
                    tmdb_info = TMDBApi(apikey).search_movie(search_title)
                    if tmdb_info:
                        logger.debug(f"TMDB info: {tmdb_info}")
                        logger.info("success getting info from TMDB")
                        if tmdb_info.poster_path:
                            image_id = FileParser._try_save_cover_from_url(
                                tmdb_info.poster_url
                            )
                        title = tmdb_info.title
                        description = tmdb_info.overview
                        date = tmdb_info.release_date
                        tags = tmdb_info.genres
                        movie_success = True

            if not image_id:
                image_id = FileParser._extract_video_frame(container)

            audio_tracks = []
            for stream in container.streams:
                if stream.type == "audio":
                    audio_tracks.append(getattr(stream, "language", "und"))

            metadata = {
                "title": title,
                "duration": int(float(container.duration) / 1000000)
                if container.duration
                else 0,
                "width": video_stream.width,
                "height": video_stream.height,
                "frame_rate": float(video_stream.average_rate or 0),
                "codec": FileParser._get_video_codec(video_stream.codec.name),
                "format": file_path.suffix.lstrip(".").lower(),
                "audio_tracks": audio_tracks,
                "thumbnail": image_id,
                "ismovie": movie_success,
                "isanime": anime_success,
                "description": description,
                "season_number": season_number,
                "date": date,
                "tags": tags,
                "episode_number": episode_number,
                "original_title": original_title,
                "total_episodes": total_episodes,
                "cover_url": cover_url,
            }

            container.close()
            return metadata

        except Exception as e:
            logger.error(f"Error parsing video file: {e}")
            return {}

    @staticmethod
    def _get_audio_codec(extension: str) -> str:
        codec_map = {
            ".mp3": "mp3",
            ".flac": "flac",
            ".m4a": "aac",
            ".ogg": "ogg",
            ".opus": "opus",
            ".wav": "wav",
        }
        return codec_map.get(extension.lower(), "unknown")

    @classmethod
    def _try_save_cover_from_url(cls, image_url: str) -> str | None:
        try:
            return cls.save_cover_art_from_url(image_url)
        except Exception as e:
            logger.error(f"Error downloading cover {image_url}: {e}")
            return None

    @classmethod
    def _extract_video_frame(cls, container) -> str | None:
        try:
            container.seek(int((container.duration or 0) * 0.1))
            for frame in container.decode(video=0):
                img = frame.to_image()
                img.thumbnail((500, 500))
                cls.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
                image_id = f"{uuid4()}.jpg"
                img.save(str(cls.IMAGES_DIR / image_id), "JPEG", quality=85)
                return image_id
        except Exception as e:
            logger.error(f"Error extracting cover: {e}")
        return None

    @staticmethod
    def _get_video_codec(codec_name: str) -> str:
        codec_map = {
            "h264": "h264",
            "hevc": "h265",
            "h265": "h265",
            "vp9": "vp9",
            "av1": "av1",
            "libdav1d": "av1",
            "libaom-av1": "av1",
        }
        return codec_map.get((codec_name or "").lower(), "unknown")
