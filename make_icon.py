#!/usr/bin/env python3
"""Generate app.ico — run once before building the exe, or let chat.py do it at startup."""
import math
import struct
import zlib
from pathlib import Path

SIZE   = 32
BG     = (0x1a, 0x1a, 0x1a, 0xff)   # dark background
FG     = (0xda, 0x77, 0x56, 0xff)   # Claude orange
CX = CY = SIZE / 2
R_MAX   = 13.5
R_MIN   = 2.8
HALF_W  = 2.1
SPOKES  = 6


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    body = tag + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def make_icon(dest: Path = Path("app.ico")) -> None:
    pixels = []
    for y in range(SIZE):
        row = []
        for x in range(SIZE):
            dx, dy = x - CX + 0.5, y - CY + 0.5
            r = math.hypot(dx, dy)
            color = BG
            if R_MIN <= r <= R_MAX:
                for i in range(SPOKES):
                    a = math.pi * i / SPOKES
                    if abs(-dx * math.sin(a) + dy * math.cos(a)) < HALF_W:
                        color = FG
                        break
            row.append(color)
        pixels.append(row)

    ihdr = struct.pack(">II", SIZE, SIZE) + bytes([8, 6, 0, 0, 0])
    raw  = b"".join(b"\x00" + bytes(c for px in row for c in px) for row in pixels)
    png  = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"IDAT", zlib.compress(raw))
        + _png_chunk(b"IEND", b"")
    )
    ico = (
        struct.pack("<HHH", 0, 1, 1)
        + struct.pack("<BBBBHHII", SIZE, SIZE, 0, 0, 1, 32, len(png), 22)
        + png
    )
    dest.write_bytes(ico)
    print(f"Created {dest}  ({len(ico)} bytes)")


if __name__ == "__main__":
    make_icon()
