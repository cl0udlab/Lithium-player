from pydantic import BaseModel
from yt_dlp import YoutubeDL
from core.logger import logger
from typing import Optional
from models import StreamPlatform


def detect_url_type(url: str) -> StreamPlatform:
    try:
        ydl = YoutubeDL()
        ie_result = ydl.extract_info(url, download=False, process=False)

        if ie_result is None:
            return StreamPlatform.UNKNOWN

        extractor_key = ie_result.get("extractor_key", "").lower()

        if "youtube" in extractor_key:
            return StreamPlatform.YOUTUBE
        elif "bilibili" in extractor_key:
            return StreamPlatform.BILIBILI
        elif "soundcloud" in extractor_key:
            return StreamPlatform.SOUNDCLOUD
        else:
            return StreamPlatform.UNKNOWN

    except Exception:
        return StreamPlatform.UNKNOWN


class StreamInfo(BaseModel):
    url: str
    title: str
    thumbnail: Optional[str] = None
    duration: Optional[int] = None


class MusicStream:
    def __init__(self, url: str):
        self.url = url
        self.type: StreamPlatform = detect_url_type(url)
        self.yt_ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }
        self.bilibili_ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "m4a",
                    "preferredquality": "192",
                }
            ],
        }
        self.option = self._get_option()

    def _get_option(self) -> dict:
        match self.type:
            case StreamPlatform.YOUTUBE:
                return self.yt_ydl_opts
            case StreamPlatform.BILIBILI:
                return self.bilibili_ydl_opts
            case _:
                return self.yt_ydl_opts

    def get_stream_info(self) -> StreamInfo:
        try:
            with YoutubeDL(self.option) as ydl:
                info = ydl.extract_info(self.url, download=False)
                if not info:
                    raise ValueError("無法取得stream資訊")

                return StreamInfo(
                    url=info.get("url", ""),
                    title=info.get("title", ""),
                    thumbnail=info.get("thumbnail", None),
                    duration=int(info.get("duration", 0)),
                )

        except Exception as e:
            logger.error(f"取得stream失敗: {str(e)}")
            return StreamInfo(url="", title="")

    def download(self, output_path: str) -> bool:
        try:
            opts = self.option.copy()
            template = f"{output_path}/%(title)s.%(ext)s"

            postprocessors: list = opts.get("postprocessors", [])
            postprocessors.extend(
                [
                    {"key": "EmbedThumbnail"},
                    {
                        "key": "FFmpegMetadata",
                        "add_metadata": True,
                    },
                    {
                        "key": "MetadataFromField",
                        "formats": ["title", "uploader"],
                        "fields": {
                            "title": "title",
                            "artist": "uploader",
                            "comment": f"Downloaded from {self.type.value}",
                            "source": self.url,
                        },
                    },
                ]
            )
            opts.update(
                {
                    "outtmpl": template,
                    "path": output_path,
                    "writethumbnail": True,
                    "postprocessors": postprocessors,
                    "add_metadata": True,
                    "parse_metadata": True,
                }
            )

            with YoutubeDL(self.option) as ydl:
                ydl.download([self.url])
                return True
        except Exception as e:
            logger.error(f"下載失敗: {str(e)}")
            return False


if __name__ == "__main__":
    url = "https://www.bilibili.com/video/BV1BZq7YmEus/"
    stream = MusicStream(url)
    print(stream.get_stream_info())
