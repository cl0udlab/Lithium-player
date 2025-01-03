from datetime import datetime
from pathlib import Path
from typing import Union
from tinytag import TinyTag
import av
from enum import Enum
from uuid import uuid4
from ebooklib import epub
from mobi import Mobi
from PyPDF2 import PdfReader
from core.logger import logger
from core.musiclyrics import get_lrclib
from core.musicparser import (
    search_track,
    search_album,
    parse_album_info,
    parse_track_info,
)
from core.filenameparse import parse_filename
from core.animeparser import get_from_Bangumi
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
        image_data = requests.get(image_url).content
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
    def parse_file(file_path: Union[str, Path]) -> dict:
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
            return {**base_info, **FileParser._parse_video(file_path)}
        elif file_type == FileType.TEXT:
            return {**base_info, **FileParser._parse_text(file_path)}
        else:
            return base_info

    @staticmethod
    def _parse_text(file_path: Path) -> dict:
        try:
            if file_path.suffix == ".epub":
                book = epub.read_epub(file_path)
                metadata = book.get_metadata()
                return {
                    "pages": len(book.get_items_of_type("page")),
                    "author": metadata.get("author"),
                    "publisher": metadata.get("publisher"),
                    "format": "epub",
                }
            elif file_path.suffix == ".mobi":
                book = Mobi(file_path)
                return {
                    "pages": book.get_pages(),
                    "author": book.get_author(),
                    "publisher": book.get_publisher(),
                    "format": "mobi",
                }
            elif file_path.suffix == ".pdf":
                reader = PdfReader(file_path)
                metadata = reader.metadata
                return {
                    "pages": len(reader.pages),
                    "author": metadata.get("/Author", "Unknown"),
                    "publisher": metadata.get("/Producer", "Unknown"),
                    "format": "pdf",
                }
            else:
                return {
                    "pages": 0,
                    "author": "Unknown",
                    "publisher": "Unknown",
                    "format": "txt",
                }
        except Exception as e:
            logger.error(f"Error parsing text file: {e}")
            return {}

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
                cover_art_id = FileParser.save_cover_art_from_url(
                    online_track.cover_art
                )

            lyrics = get_lrclib(tag.album, tag.artist, tag.title)

            # TODO: 沒有時間修 以後再重構
            return {
                "title": tag.title or online_track.title
                if online_track
                else file_path.stem,
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
    def _parse_video(file_path: Path) -> dict:
        try:
            logger.info(f"Parsing video file: {file_path}")
            file_path_str = str(file_path.resolve())
            container = av.open(str(file_path_str))
            video_stream: av.VideoStream = next(
                s for s in container.streams if s.type == "video"
            )
            cover_path = None
            image_id = str(uuid4())
            title = file_path.stem
            description = ""
            season_number = ""
            date = ""
            episode_number = 1
            tags = []
            anime_success = False
            movie_success = False
            parse_file = parse_filename(file_path.stem)
            logger.info(
                f"Parse file name status: {'failed' if parse_file.parse_failed else 'success'}"
            )
            if parse_file.parse_failed:
                try:
                    container.seek(0)
                    for frame in container.decode(video=0):
                        img = frame.to_image()
                        covers_dir = Path("data/images")
                        covers_dir.mkdir(parents=True, exist_ok=True)
                        cover_path = covers_dir / f"{image_id}.jpg"
                        img.thumbnail((500, 500))
                        img.save(str(cover_path), "JPEG", quality=85)
                        break
                    image_id = image_id + ".jpg"
                except Exception as e:
                    logger.error(f"Error extracting cover: {e}")
            else:
                logger.info("Getting info from bangumi")
                bangumi_info = get_from_Bangumi(
                    parse_file.name_zh or parse_file.name_jp or parse_file.name_en
                )
                if bangumi_info:
                    logger.debug(f"Bangumi info: {bangumi_info}")
                    logger.info("success getting info from bangumi")
                    image_id = FileParser.save_cover_art_from_url(
                        bangumi_info.images.large
                    )
                    title = bangumi_info.name_cn or bangumi_info.name
                    description = bangumi_info.summary
                    season_number = parse_file.season
                    date = bangumi_info.date
                    tags = [tag.name for tag in bangumi_info.tags]
                    episode_number = parse_file.episode
                    anime_success = True
                else:
                    logger.info("Getting info from TMDB")
                    apikey = load_setting().tmd_api_key
                    if apikey == "":
                        logger.error("TMDB API key not set")
                    else:
                        tmdb_info = TMDBApi(apikey).search_movie(
                            parse_file.name_zh
                            or parse_file.name_jp
                            or parse_file.name_en
                        )
                        if tmdb_info:
                            logger.debug(f"TMDB info: {tmdb_info}")
                            logger.info("success getting info from TMDB")
                            image_id = FileParser.save_cover_art_from_url(
                                tmdb_info.poster_path
                            )
                            title = tmdb_info.title
                            description = tmdb_info.overview
                            date = tmdb_info.release_date
                            tags = tmdb_info.genres
                            movie_success = True
                        else:
                            try:
                                container.seek(0)
                                for frame in container.decode(video=0):
                                    img = frame.to_image()
                                    covers_dir = Path("data/images")
                                    covers_dir.mkdir(parents=True, exist_ok=True)
                                    cover_path = covers_dir / f"{image_id}.jpg"
                                    img.thumbnail((500, 500))
                                    img.save(str(cover_path), "JPEG", quality=85)
                                    break
                                image_id = image_id + ".jpg"
                            except Exception as e:
                                logger.error(f"Error extracting cover: {e}")

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
                "codec": video_stream.codec.name,
                "format": file_path.suffix.lstrip("."),
                "audio_tracks": audio_tracks,
                "thumbnail": image_id,
                "ismovie": movie_success,
                "isanime": anime_success,
                "description": description,
                "season_number": season_number,
                "date": date,
                "tags": tags,
                "episode_number": episode_number,
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
