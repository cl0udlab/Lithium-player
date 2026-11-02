"""jixunmoe-go/qrc (MIT License, Copyright (c) 2023 Jixun Wu)
https://github.com/jixunmoe-go/qrc
"""

import html
import re
import zlib
from .base import LyricLine, LyricWord


QRC_KEYS = [(b"!@#)(NHL", False), (b"123ZXC!@", True), (b"!@#)(*$%", False)]

# fmt: off
KEY_RND_SHIFTS = [1, 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 1]
LARGE_STATE_SHIFTS = [26, 20, 14, 8, 58, 52, 46, 40]
SBOXES = [
    [14, 0, 4, 15, 13, 7, 1, 4, 2, 14, 15, 2, 11, 13, 8, 1, 3, 10, 10, 6, 6, 12, 12, 11, 5, 9, 9, 5, 0, 3, 7, 8,
     4, 15, 1, 12, 14, 8, 8, 2, 13, 4, 6, 9, 2, 1, 11, 7, 15, 5, 12, 11, 9, 3, 7, 14, 3, 10, 10, 0, 5, 6, 0, 13],
    [15, 3, 1, 13, 8, 4, 14, 7, 6, 15, 11, 2, 3, 8, 4, 15, 9, 12, 7, 0, 2, 1, 13, 10, 12, 6, 0, 9, 5, 11, 10, 5,
     0, 13, 14, 8, 7, 10, 11, 1, 10, 3, 4, 15, 13, 4, 1, 2, 5, 11, 8, 6, 12, 7, 6, 12, 9, 0, 3, 5, 2, 14, 15, 9],
    [10, 13, 0, 7, 9, 0, 14, 9, 6, 3, 3, 4, 15, 6, 5, 10, 1, 2, 13, 8, 12, 5, 7, 14, 11, 12, 4, 11, 2, 15, 8, 1,
     13, 1, 6, 10, 4, 13, 9, 0, 8, 6, 15, 9, 3, 8, 0, 7, 11, 4, 1, 15, 2, 14, 12, 3, 5, 11, 10, 5, 14, 2, 7, 12],
    [7, 13, 13, 8, 14, 11, 3, 5, 0, 6, 6, 15, 9, 0, 10, 3, 1, 4, 2, 7, 8, 2, 5, 12, 11, 1, 12, 10, 4, 14, 15, 9,
     10, 3, 6, 15, 9, 0, 0, 6, 12, 10, 11, 10, 7, 13, 13, 8, 15, 9, 1, 4, 3, 5, 14, 11, 5, 12, 2, 7, 8, 2, 4, 14],
    [2, 14, 12, 11, 4, 2, 1, 12, 7, 4, 10, 7, 11, 13, 6, 1, 8, 5, 5, 0, 3, 15, 15, 10, 13, 3, 0, 9, 14, 8, 9, 6,
     4, 11, 2, 8, 1, 12, 11, 7, 10, 1, 13, 14, 7, 2, 8, 13, 15, 6, 9, 15, 12, 0, 5, 9, 6, 10, 3, 4, 0, 5, 14, 3],
    [12, 10, 1, 15, 10, 4, 15, 2, 9, 7, 2, 12, 6, 9, 8, 5, 0, 6, 13, 1, 3, 13, 4, 14, 14, 0, 7, 11, 5, 3, 11, 8,
     9, 4, 14, 3, 15, 2, 5, 12, 2, 9, 8, 5, 12, 15, 3, 10, 7, 11, 0, 14, 4, 1, 10, 7, 1, 6, 13, 0, 11, 8, 6, 13],
    [4, 13, 11, 0, 2, 11, 14, 7, 15, 4, 0, 9, 8, 1, 13, 10, 3, 14, 12, 3, 9, 5, 7, 12, 5, 2, 10, 15, 6, 8, 1, 6,
     1, 6, 4, 11, 11, 13, 13, 8, 12, 1, 3, 4, 7, 10, 14, 7, 10, 9, 15, 5, 6, 0, 8, 15, 0, 14, 5, 2, 9, 3, 2, 12],
    [13, 1, 2, 15, 8, 13, 4, 8, 6, 10, 15, 3, 11, 7, 1, 4, 10, 12, 9, 5, 3, 6, 14, 11, 5, 0, 0, 14, 12, 9, 7, 2,
     7, 2, 11, 1, 4, 14, 1, 7, 9, 4, 12, 10, 14, 8, 2, 13, 0, 15, 6, 12, 10, 9, 13, 0, 15, 3, 3, 5, 5, 6, 8, 11],
]
P_BOX = [15, 6, 19, 20, 28, 11, 27, 16, 0, 14, 22, 25, 4, 17, 30, 9,
         1, 7, 23, 13, 31, 26, 2, 8, 18, 12, 29, 5, 21, 10, 3, 24]
IP = [57, 49, 41, 33, 25, 17, 9, 1, 59, 51, 43, 35, 27, 19, 11, 3,
      61, 53, 45, 37, 29, 21, 13, 5, 63, 55, 47, 39, 31, 23, 15, 7,
      56, 48, 40, 32, 24, 16, 8, 0, 58, 50, 42, 34, 26, 18, 10, 2,
      60, 52, 44, 36, 28, 20, 12, 4, 62, 54, 46, 38, 30, 22, 14, 6]
IP_INV = [39, 7, 47, 15, 55, 23, 63, 31, 38, 6, 46, 14, 54, 22, 62, 30,
          37, 5, 45, 13, 53, 21, 61, 29, 36, 4, 44, 12, 52, 20, 60, 28,
          35, 3, 43, 11, 51, 19, 59, 27, 34, 2, 42, 10, 50, 18, 58, 26,
          33, 1, 41, 9, 49, 17, 57, 25, 32, 0, 40, 8, 48, 16, 56, 24]
KEY_PERMUTATION = [56, 48, 40, 32, 24, 16, 8, 0, 57, 49, 41, 33, 25, 17,
                   9, 1, 58, 50, 42, 34, 26, 18, 10, 2, 59, 51, 43, 35,
                   62, 54, 46, 38, 30, 22, 14, 6, 61, 53, 45, 37, 29, 21,
                   13, 5, 60, 52, 44, 36, 28, 20, 12, 4, 27, 19, 11, 3]
KEY_COMPRESSION = [13, 16, 10, 23, 0, 4, 2, 27, 14, 5, 20, 9, 22, 18, 11, 3,
                   25, 7, 15, 6, 26, 19, 12, 1, 45, 56, 35, 41, 51, 59, 34, 44,
                   55, 49, 37, 52, 48, 53, 43, 60, 38, 57, 50, 46, 54, 40, 33, 36]
KEY_EXPANSION = [31, 0, 1, 2, 3, 4, 3, 4, 5, 6, 7, 8, 7, 8, 9, 10,
                 11, 12, 11, 12, 13, 14, 15, 16, 15, 16, 17, 18, 19, 20, 19, 20,
                 21, 22, 23, 24, 23, 24, 25, 26, 27, 28, 27, 28, 29, 30, 31, 0]
# fmt: on


def _bit_pos(idx: int) -> int:
    """des_shift_table_cache: 0~31 對應低 32 位 (由高到低), 32~63 對應高 32 位"""
    idx &= 0x3F
    return 31 - idx if idx < 32 else 95 - idx


def _compile(pairs: list[tuple[int, int]], src_bytes: int) -> list[list[int]]:
    """把 map_bit 的逐位元置換預先算成每個來源 byte 一張 256 格的表"""
    tables = [[0] * 256 for _ in range(src_bytes)]
    for check, out_bit in pairs:
        byte, bit = divmod(_bit_pos(check), 8)
        for value in range(256):
            if value >> bit & 1:
                tables[byte][value] |= 1 << out_bit
    return tables


def _u64_pairs(table: list[int]) -> list[tuple[int, int]]:
    """map_u64: 前半張表填低 32 位, 後半張表填高 32 位"""
    mid = len(table) // 2
    return [(v, 31 - i) for i, v in enumerate(table[:mid])] + [
        (v, 63 - i) for i, v in enumerate(table[mid:])
    ]


def _apply(tables: list[list[int]], value: int) -> int:
    result = 0
    for i, table in enumerate(tables):
        result |= table[(value >> (8 * i)) & 0xFF]
    return result


_IP = _compile(_u64_pairs(IP), 8)
_IP_INV = _compile(_u64_pairs(IP_INV), 8)
_KEY_PERMUTATION = _compile(_u64_pairs(KEY_PERMUTATION), 8)
_KEY_COMPRESSION = _compile(_u64_pairs(KEY_COMPRESSION), 8)
_KEY_EXPANSION = _compile(_u64_pairs(KEY_EXPANSION), 8)
_P_BOX = _compile([(v, 31 - i) for i, v in enumerate(P_BOX)], 4)


def _update_param(param: int, shift_left: int) -> int:
    return (
        (param << shift_left) | ((param >> (28 - shift_left)) & 0xFFFFFFF0)
    ) & 0xFFFFFFFF


def _subkeys(key: bytes, encrypt: bool) -> list[int]:
    param = _apply(_KEY_PERMUTATION, int.from_bytes(key[:8], "little"))
    param_c, param_d = param & 0xFFFFFFFF, param >> 32
    subkeys = [0] * 16
    for i, shift_left in enumerate(KEY_RND_SHIFTS):
        param_c = _update_param(param_c, shift_left)
        param_d = _update_param(param_d, shift_left)
        subkeys[i if encrypt else 15 - i] = _apply(
            _KEY_COMPRESSION, (param_d << 32) | param_c
        )
    return subkeys


def _crypt_proc(state: int, key: int) -> int:
    hi32, lo32 = state >> 32, state & 0xFFFFFFFF
    state = _apply(_KEY_EXPANSION, (hi32 << 32) | hi32) ^ key
    next_lo32 = 0
    for sbox, shift in zip(SBOXES, LARGE_STATE_SHIFTS):
        next_lo32 = (next_lo32 << 4) | sbox[(state >> shift) & 0x3F]
    next_lo32 = _apply(_P_BOX, next_lo32) ^ lo32
    return (next_lo32 << 32) | hi32


def _transform_block(value: int, subkeys: list[int]) -> int:
    state = _apply(_IP, value)
    for key in subkeys:
        state = _crypt_proc(state, key)
    state = ((state >> 32) | (state << 32)) & 0xFFFFFFFFFFFFFFFF
    return _apply(_IP_INV, state)


_SCHEDULES = [_subkeys(key, encrypt) for key, encrypt in QRC_KEYS]


def decrypt_qrc(encrypted_hex: str) -> str:
    """解密 GetPlayLyricInfo 回傳的 hex 字串 (lyric / trans / roma), 失敗丟 ValueError"""
    data = bytes.fromhex(encrypted_hex)
    if len(data) % 8:
        raise ValueError("QRC 長度不是 8 的倍數")
    out = bytearray()
    for i in range(0, len(data), 8):
        value = int.from_bytes(data[i : i + 8], "little")
        for subkeys in _SCHEDULES:
            value = _transform_block(value, subkeys)
        out += value.to_bytes(8, "little")
    try:
        text = zlib.decompress(bytes(out))
    except zlib.error as e:
        raise ValueError(f"QRC 解壓縮失敗: {e}") from e
    return text.decode("utf-8-sig", errors="replace")


QRC_CONTENT = re.compile(r'LyricContent="(.*?)"\s*/>', re.S)
QRC_LINE = re.compile(r"^\[(\d+),(\d+)\](.*)$")

QRC_WORD = re.compile(r"(.*?)\((\d+),(\d+)\)", re.S)


def is_qrc(text: str) -> bool:
    return "<QrcInfos" in text or bool(re.search(r"^\[\d+,\d+\]", text, re.M))


def parse_qrc(text: str) -> list[LyricLine]:
    match = QRC_CONTENT.search(text)
    content = html.unescape(match.group(1)) if match else text
    lines = []
    for raw in content.splitlines():
        line_match = QRC_LINE.match(raw.strip())
        if not line_match:
            continue
        start, duration, body = line_match.groups()
        timed = QRC_WORD.findall(body)
        words = [
            LyricWord(int(s) / 1000, (int(s) + int(d)) / 1000, word)
            for word, s, d in timed
            if word
        ]

        text = "".join(w.text for w in words) if timed else body
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            lines.append(
                LyricLine(
                    start=int(start) / 1000,
                    end=(int(start) + int(duration)) / 1000,
                    text=text,
                    words=words,
                )
            )
    lines.sort(key=lambda line: line.start)
    return lines
