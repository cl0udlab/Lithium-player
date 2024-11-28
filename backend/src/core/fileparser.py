from datetime import datetime
from pathlib import Path
from typing import Dict, Union
from tinytag import TinyTag
import av
from enum import Enum


class FileType(str, Enum):
    MUSIC = "music"
    VIDEO = "video"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


class FileParser:
    SUPPORT_MUSIC = {".mp3", ".flac", ".aac", ".ogg", ".opus", ".wav"}
    SUPPORT_VIDEO = {".mp4", ".mkv", ".webm", ".avi", ".flv", ".mov", ".wmv"}

    @staticmethod
    def get_file_type(file_path: Union[str, Path]) -> FileType:
        file_path = Path(file_path)
        extension = file_path.suffix.lower()

        if extension in FileParser.SUPPORT_MUSIC:
            return FileType.MUSIC
        elif extension in FileParser.SUPPORT_VIDEO:
            return FileType.VIDEO
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
            "created_at": datetime.fromtimestamp(file_stat.st_ctime),
            "updated_at": datetime.fromtimestamp(file_stat.st_mtime),
        }

        if file_type == FileType.MUSIC:
            return {**base_info, **FileParser._parse_music(file_path)}
        elif file_type == FileType.VIDEO:
            return {**base_info, **FileParser._parse_video(file_path)}
        else:
            return base_info

    @staticmethod
    def _parse_music(file_path: Path) -> Dict:
        try:
            tag = TinyTag.get(file_path)

            return {
                "title": tag.title or file_path.stem,
                "duration": int(tag.duration or 0),
                "bitrate": tag.bitrate or 0,
                "sample_rate": tag.samplerate or 0,
                "artist": tag.artist,
                "album": tag.album,
                "album_artist": tag.albumartist,
                "composer": tag.composer,
                "genre": tag.genre,
                "year": tag.year,
                "track_number": tag.track,
                "disc_number": tag.disc,
                "audio_type": "stereo" if (tag.channels or 0) > 1 else "mono",
                "codec": FileParser._get_audio_codec(file_path.suffix),
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
                    audio_tracks.append(
                        {
                            "language": getattr(stream, "language", "und"),
                            "codec": stream.codec_name,
                        }
                    )

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
