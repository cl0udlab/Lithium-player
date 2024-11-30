from pathlib import Path
import av
import subprocess
from typing import List, Tuple
import math


def get_video_info(video: av.container.InputContainer) -> Tuple[int, int, float]:
    """獲取影片資訊"""
    stream = video.streams.video[0]
    return stream.width, stream.height, float(stream.duration * stream.time_base)


def create_resolutions(width: int, height: int) -> List[Tuple[int, int]]:
    """計算需要的解析度"""
    resolutions = []
    standard_heights = [2160, 1440, 1080, 720, 480]
    aspect_ratio = width / height

    resolutions.append((width, height))

    for h in standard_heights:
        if h < height:
            w = math.floor(h * aspect_ratio)
            w = w - (w % 2)

            if (w, h) not in resolutions:
                resolutions.append((w, h))

    resolutions.sort(key=lambda x: x[1], reverse=True)
    return resolutions


def create_hls(videopath: Path, output_dir: Path):
    """將影片轉換為 HLS 格式"""
    video = av.open(str(videopath))
    width, height, duration = get_video_info(video)
    resolutions = create_resolutions(width, height)

    output_dir.mkdir(parents=True, exist_ok=True)

    master_playlist = "#EXTM3U\n"

    for res_width, res_height in resolutions:
        variant_name = f"{res_height}p"
        variant_dir = output_dir / variant_name
        variant_dir.mkdir(exist_ok=True)

        cmd = [
            "ffmpeg",
            "-hwaccel",
            "auto",
            "-i",
            str(videopath),
            "-vf",
            f"scale={res_width}:{res_height}",
            "-c:v",
            "h264",
            "-c:a",
            "aac",
            "-b:v",
            f"{res_height * 2}k",
            "-hls_time",
            "10",
            "-hls_playlist_type",
            "vod",
            "-hls_segment_filename",
            f"{variant_dir}/%03d.ts",
            f"{variant_dir}/playlist.m3u8",
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"處理 {res_height}p 解析度完成")

            if not (variant_dir / "playlist.m3u8").exists():
                raise Exception(f"無法產生 {res_height}p 的播放列表")

            master_playlist += f"#EXT-X-STREAM-INF:BANDWIDTH={res_height * 2000},RESOLUTION={res_width}x{res_height}\n"
            master_playlist += f"{variant_name}/playlist.m3u8\n"

        except subprocess.CalledProcessError as e:
            print(f"處理 {res_height}p 時發生錯誤:")
            print(f"錯誤輸出: {e.stderr}")
            continue
        except Exception as e:
            print(f"發生錯誤: {str(e)}")
            continue

    with open(output_dir / "master.m3u8", "w") as f:
        f.write(master_playlist)

    video.close()


if __name__ == "__main__":
    video_path = Path("/Users/phillychi3/Movies/1335904253-1-192.mp4")
    output_path = Path("/Users/phillychi3/Movies/HLS")
    create_hls(video_path, output_path)
