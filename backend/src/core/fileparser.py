from datetime import datetime
from pathlib import Path
from typing import Dict, Union
from tinytag import TinyTag
import av
from enum import Enum
from uuid import uuid4
from ebooklib import epub
from mobi import Mobi
from PyPDF2 import PdfReader


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
    def parse_file(file_path: Union[str, Path]) -> Dict:
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
    def _parse_text(file_path: Path) -> Dict:
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
            print(f"Error parsing text file: {e}")
            return {}

    @staticmethod
    def _parse_music(file_path: Path) -> Dict:
        try:
            tag = TinyTag.get(file_path, image=True)
            cover_art = tag.images.any
            cover_art_id = None
            if cover_art and cover_art.data:
                cover_art_id = FileParser.save_cover_art(cover_art.data)

            return {
                "title": tag.title or file_path.stem,
                "duration": int(tag.duration or 0),
                "bitrate": tag.bitrate or 0,
                "sample_rate": tag.samplerate or 0,
                "artist": tag.artist,
                "album": tag.album,
                "album_artist": tag.albumartist if tag.albumartist else tag.artist,
                "composer": tag.composer,
                "genre": tag.genre,
                "year": tag.year,
                "track_number": tag.track,
                "disc_number": tag.disc,
                "audio_type": "stereo" if (tag.channels or 0) > 1 else "mono",
                "codec": FileParser._get_audio_codec(file_path.suffix),
                "cover_art": cover_art_id,
            }
        except Exception as e:
            print(f"Error parsing music file: {e}")
            return {}

    @staticmethod
    def _parse_video(file_path: Path) -> Dict:
        try:
            container = av.open(str(file_path))

            video_stream: av.VideoStream = next(
                s for s in container.streams if s.type == "video"
            )
            audio_tracks = []
            for stream in container.streams:
                if stream.type == "audio":
                    audio_tracks.append(getattr(stream, "language", "und"))

            metadata = {
                "title": file_path.stem,
                "duration": int(float(container.duration) / 1000000)
                if container.duration
                else 0,
                "width": video_stream.width,
                "height": video_stream.height,
                "frame_rate": float(video_stream.average_rate or 0),
                "codec": video_stream.codec.name,
                "format": file_path.suffix.lstrip("."),
                "audio_tracks": audio_tracks,
            }

            container.close()
            return metadata

        except Exception as e:
            print(f"Error parsing video file: {e}")
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
