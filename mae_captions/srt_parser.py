import re
from dataclasses import dataclass, field
from pathlib import Path

import chardet

TIMECODE_RE = re.compile(r"(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})")


@dataclass
class Entry:
    index: int
    start: str
    end: str
    lines: list[str] = field(default_factory=list)


def timecode_to_ms(tc: str) -> int:
    h, m, rest = tc.split(":")
    s, ms = rest.replace(",", ".").split(".")
    return int(h) * 3_600_000 + int(m) * 60_000 + int(s) * 1_000 + int(ms)


def ms_to_timecode(ms: int) -> str:
    h = ms // 3_600_000
    ms %= 3_600_000
    m = ms // 60_000
    ms %= 60_000
    s = ms // 1_000
    ms %= 1_000
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def parse_srt(path: Path) -> list[Entry]:
    raw = path.read_bytes()
    detected = chardet.detect(raw)
    encoding = detected.get("encoding") or "utf-8"
    text = raw.decode(encoding, errors="replace")
    text = text.lstrip("﻿")
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    entries: list[Entry] = []
    blocks = re.split(r"\n{2,}", text.strip())

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue

        try:
            index = int(lines[0].strip())
        except ValueError:
            continue

        tc_match = TIMECODE_RE.match(lines[1].strip())
        if not tc_match:
            continue

        start = tc_match.group(1).replace(".", ",")
        end = tc_match.group(2).replace(".", ",")
        text_lines = [l for l in lines[2:]]  # noqa: E741

        entries.append(Entry(index=index, start=start, end=end, lines=text_lines))

    return entries


def serialize_srt(entries: list[Entry], path: Path, bom: bool = False) -> None:
    parts: list[str] = []
    for i, entry in enumerate(entries, 1):
        parts.append(str(i))
        parts.append(f"{entry.start} --> {entry.end}")
        parts.extend(entry.lines if entry.lines else [""])
        parts.append("")

    content = "\n".join(parts).rstrip("\n") + "\n"

    if bom:
        path.write_bytes(b"\xef\xbb\xbf" + content.encode("utf-8"))
    else:
        path.write_text(content, encoding="utf-8")
