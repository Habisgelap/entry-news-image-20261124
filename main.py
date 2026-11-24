#!/usr/bin/env python3
"""News image: the world news of Tuesday 24 November 2026 in one image.

Draws a deterministic 1024x1024 newspaper front page with the day's eight
verified stories and writes it to /output/entry.png.

Pure standard library: the image is rasterised by hand and encoded as PNG
with zlib, so it runs in the grader's no-network sandbox with nothing
installed. The output bytes are identical on every run.
"""

import binascii
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (247, 243, 234)
INK = (20, 20, 20)
NAVY = (20, 33, 61)
GOLD = (200, 155, 60)
RED = (180, 35, 24)
TEAL = (14, 110, 110)
GREEN = (26, 127, 55)
GREY = (90, 90, 90)
WHITE = (255, 255, 255)

# 5x7 bitmap font, one row per string, '#' = on. Uppercase, digits and the
# punctuation this page uses.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "a": ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    "b": ("10000", "10000", "10110", "11001", "10001", "10001", "11110"),
    "c": ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    "d": ("00001", "00001", "01101", "10011", "10001", "10001", "01111"),
    "e": ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    "f": ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    "g": ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    "h": ("10000", "10000", "10110", "11001", "10001", "10001", "10001"),
    "i": ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    "j": ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    "k": ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    "l": ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    "m": ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    "n": ("00000", "00000", "10110", "11001", "10001", "10001", "10001"),
    "o": ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    "p": ("00000", "00000", "11110", "10001", "11110", "10000", "10000"),
    "q": ("00000", "00000", "01101", "10011", "01111", "00001", "00001"),
    "r": ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    "s": ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    "t": ("01000", "01000", "11100", "01000", "01000", "01000", "00110"),
    "u": ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    "v": ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    "w": ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    "x": ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    "y": ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    "z": ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "\u2022": ("00000", "00000", "01100", "01100", "01100", "00000", "00000"),
}

# The day's eight verified stories (events of, or first reported on,
# Tuesday 24 November 2026).
LEAD = {
    "kicker": "TECH - LEAD STORY",
    "headline": "NVIDIA BRINGS BACK HUANG",
    "summary": "Board reinstates Jensen Huang as CEO on Monday, 11 days after his ouster, after Trump pressed for his return.",
}
STORIES = [
    {
        "kicker": "WAR",
        "headline": "UKRAINE CLAIMS IT SANK A RUSSIAN WARSHIP OFF LIBYA",
        "summary": "Kyiv says its forces sank the corvette off the Libyan coast, taking the war to Russian assets far from Ukraine.",
    },
    {
        "kicker": "TECH",
        "headline": "US TO BLACKLIST MEGASPEED OVER NVIDIA CHIPS",
        "summary": "Washington moves to put the Asian AI firm on its Entity List.",
    },
    {
        "kicker": "MARKETS",
        "headline": "TRUMP BLAMES DEMOCRATS FOR $1 TRILLION ROUT",
        "summary": "The president blames the opposition after Wall Street's rout following the midterm results.",
    },
    {
        "kicker": "TECH",
        "headline": "WAYMO PULLS DRIVERLESS TAXIS OFF FREEWAYS",
        "summary": "The robotaxi firm suspends freeway trips after California's ban and traffic incidents.",
    },
    {
        "kicker": "MIDDLE EAST",
        "headline": "EISENKOT CALLS SETTLER ARSON 'JEWISH TERRORISM'",
        "summary": "Gadi Eisenkot condemns arson attacks on Palestinian villages in the West Bank.",
    },
    {
        "kicker": "MIGRATION",
        "headline": "MIGRANT BOAT SINKS OFF SENEGAL, DOZENS MISSING",
        "summary": "Rescuers search for survivors after a boat carrying migrants goes down.",
    },
    {
        "kicker": "GAZA",
        "headline": "GAZA CONTAMINATION REPORT: AIR, SOIL AND WATER POISONED FOR DECADES",
        "summary": "Oxfam and CEOBS warn toxins threaten life across the Strip.",
    },
]


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def rect(self, x, y, w, h, color):
        for yy in range(max(0, y), min(self.h, y + h)):
            base = (yy * self.w + max(0, x)) * 3
            for xx in range(max(0, x), min(self.w, x + w)):
                i = (yy * self.w + xx) * 3
                self.px[i:i + 3] = bytes(color)

    def text(self, s, x, y, scale, color):
        cx = x
        for ch in s:
            glyph = FONT.get(ch)
            if glyph is None:
                raise ValueError(f"no glyph for {ch!r}")
            for row, bits in enumerate(glyph):
                for col, bit in enumerate(bits):
                    if bit == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx - x

    def text_width(self, s, scale):
        return len(s) * 6 * scale

    def wrap(self, s, scale, max_w):
        lines, cur = [], ""
        for word in s.split(" "):
            trial = word if not cur else cur + " " + word
            if self.text_width(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


def chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    return c + struct.pack(">I", binascii.crc32(typ + data) & 0xFFFFFFFF)


def encode_png(canvas):
    raw = bytearray()
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * canvas.w * 3:(y + 1) * canvas.w * 3]
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def draw():
    c = Canvas(W, H, PAPER)
    # Masthead.
    c.rect(0, 0, W, 140, NAVY)
    title = "THE WORLD IN ONE IMAGE"
    tw = c.text_width(title, 7)
    c.text(title, (W - tw) // 2, 24, 7, WHITE)
    date = "TUESDAY, 24 NOVEMBER 2026"
    dw = c.text_width(date, 4)
    c.text(date, (W - dw) // 2, 92, 4, GOLD)
    c.rect(0, 140, W, 6, GOLD)
    # Lead story: chip graphic left, text right.
    c.rect(40, 160, 150, 150, GREEN)
    c.rect(52, 172, 126, 126, (18, 90, 40))
    for px in (66, 96, 126, 156):
        c.rect(px, 150, 10, 10, GOLD)
        c.rect(px, 310, 10, 10, GOLD)
    for py in (186, 216, 246, 276):
        c.rect(30, py, 10, 10, GOLD)
        c.rect(190, py, 10, 10, GOLD)
    nvda = "NVDA"
    nw = c.text_width(nvda, 5)
    c.text(nvda, 115 - nw // 2, 208, 5, WHITE)
    c.text("NASDAQ", 115 - c.text_width("NASDAQ", 2) // 2, 258, 2, GOLD)
    c.text(LEAD["kicker"], 220, 164, 3, RED)
    y = 196
    for line in c.wrap(LEAD["headline"], 5, 764):
        c.text(line, 220, y, 5, INK)
        y += 40
    y += 8
    for line in c.wrap(LEAD["summary"], 3, 764):
        c.text(line, 220, y, 3, GREY)
        y += 26
    # Divider.
    c.rect(40, 372, W - 80, 4, NAVY)
    # Grid: 6 stories in 2 columns x 3 rows. Headlines carry each story;
    # the lead and the full-width story below carry summaries.
    kicker_color = {"WAR": RED, "TECH": TEAL, "MARKETS": RED,
                    "MIDDLE EAST": RED, "MIGRATION": TEAL, "GAZA": RED}
    cells = [(40, 392), (532, 392), (40, 567), (532, 567),
             (40, 742), (532, 742)]
    for story, (x, yy) in zip(STORIES[:6], cells):
        c.text(story["kicker"], x, yy, 3, kicker_color[story["kicker"]])
        y = yy + 30
        for line in c.wrap(story["headline"], 4, 452):
            c.text(line, x, y, 4, INK)
            y += 34
    # Seventh story, full width.
    story = STORIES[6]
    c.rect(40, 886, W - 80, 2, NAVY)
    c.text(story["kicker"], 40, 898, 3, RED)
    y = 928
    for line in c.wrap(story["headline"], 4, 944):
        c.text(line, 40, y, 4, INK)
        y += 34
    y += 4
    for line in c.wrap(story["summary"], 2, 944):
        c.text(line, 40, y, 2, GREY)
        y += 18
    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    data = encode_png(draw())
    # Self-checks: valid PNG, 1024x1024, at most 1 MiB, deterministic bytes.
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    w, h = struct.unpack(">II", data[16:24])
    assert (w, h) == (1024, 1024), f"image is {w}x{h}, gate is 1024x1024 max"
    assert len(data) <= 1048576, f"image is {len(data)} bytes, gate is 1 MiB"
    assert encode_png(draw()) == data, "output is not deterministic"
    with open(path, "wb") as f:
        f.write(data)
    print(f"wrote {len(data)} bytes to {path}")


if __name__ == "__main__":
    main()
