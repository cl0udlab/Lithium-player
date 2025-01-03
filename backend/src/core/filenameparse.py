import re
from pydantic import BaseModel


class AnimeFile(BaseModel):
    name_en: str
    name_jp: str
    name_zh: str
    season: int
    episode: int
    resolution: str
    codec: str
    subtitle: str
    type: str
    parse_failed: bool = False


TYPE = ["GEKIJOUBAN", "MOVIE", "OAD", "OAV", "ONA", "OVA", "SPECIAL", "SPECIALS", "TV"]
RESOLUTION = ["480", "720", "1080", "2160", "4K"]
CODEC = ["AVC", "H264", "H265", "AAC", "FLAC", "MP3", "OGG", "AC3", "AC3"]
SUBTITLE = ["BIG5", "GB", "JP", "EN", "CH"]


def pre(name: str) -> str:
    name = name.replace("【", "[").replace("】", "]")
    name = name.replace("_", " ")
    return name


def make_re(data: list) -> re.Pattern:
    return re.compile("|".join(data))


def get_title(name: str) -> dict[str]:
    name = pre(name)
    result = {
        "name_en": "",
        "name_jp": "",
        "name_zh": "",
    }
    name = name.strip()
    name = re.sub(r"\[.*?\]|\(.*?\)", "", name)
    name = re.sub(r"\.\w+$", "", name)
    name = name.strip()
    name = re.split(r"\s*\/\s*|\s*\|\s*", name)
    for n in name:
        if re.search(r"[\u4e00-\u9fff]", n):
            result["name_zh"] = n
        elif re.search(r"[\u3040-\u309f\u30a0-\u30ff]", n):
            result["name_jp"] = n
        elif re.match(r"[A-Za-z]", n):
            result["name_en"] = n
    return result


def parse_filename(filename: str) -> AnimeFile:
    filename = pre(filename)
    blocks = [b.strip() for b in re.split(r"\[|\]", filename) if b.strip()]
    result = {
        "name_en": "",
        "name_jp": "",
        "name_zh": "",
        "season": 1,
        "episode": 0,
        "resolution": "",
        "codec": "",
        "subtitle": "",
        "type": "",
        "parse_failed": False,
    }
    result.update(**get_title(filename))
    if (
        result.get("name_en") == ""
        and result.get("name_jp") == ""
        and result.get("name_zh") == ""
    ):
        result["parse_failed"] = True
    for block in blocks[1:]:
        episode_match = re.match(r"^(?:第)?(\d{1,3})(?:話|集|$)", block)
        if episode_match:
            result["episode"] = int(episode_match.group(1))
            continue

        season_match = re.match(r"S(\d{1,2})", block, re.IGNORECASE)
        if season_match:
            result["season"] = int(season_match.group(1))
            continue

        if make_re(RESOLUTION).match(block.upper()):
            result["resolution"] = block
            continue

        codecs = make_re(CODEC).findall(block.upper())
        if codecs:
            result["codec"] = "_".join(codecs)
            continue

        if make_re(SUBTITLE).match(block.upper()):
            result["subtitle"] = block
            continue

        if make_re(TYPE).match(block.upper()):
            result["type"] = block.upper()
            continue

    return AnimeFile(**result)


if __name__ == "__main__":
    print(parse_filename("[DHR&DMG] Mondaiji [01][BIG5][720P][AVC_AAC].mp4"))
    print(
        parse_filename("[Urusai]_Bokura_Ga_Ita_01_[DVD_h264_AC3]_[BFCE1627][Fixed].mkv")
    )
    print(
        parse_filename(
            "[DMG] 劇場版 ソードアート·オンライン -プログレッシブ- 星なき夜のアリア [BDRip][AVC_AAC][720P][CHT](0BB4E0EF)"
        )
    )
    print(
        parse_filename(
            "[Lilith-Raws] 無職轉生 / Mushoku Tensei S2 [03][BIG5][1080P][AVC_AAC].mp4"
        )
    )
    print(
        parse_filename(
            "[ANK-Raws] 進撃の巨人 / Shingeki no Kyojin [01][BIG5][1080P].mkv"
        )
    )
    print(parse_filename("[SpoonSubs]_Hidamari_Sketch_x365_-_04.1_(DVD)[B6CE8458].mkv"))
