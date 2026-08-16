from dataclasses import dataclass, field

from .srt_parser import Entry, timecode_to_ms

MARKER = "<<{}>>"


@dataclass
class Chunk:
    entry_indices: list[int] = field(default_factory=list)
    source_text: str = ""
    marker_count: int = 0


def chunk_entries(
    entries: list[Entry],
    entry_texts: list[str],
    max_chunk_chars: int,
    gap_threshold_ms: int,
) -> list[Chunk]:
    if not entries:
        return []

    chunks: list[Chunk] = []
    current_indices: list[int] = []
    current_texts: list[str] = []

    def flush() -> None:
        if not current_indices:
            return
        parts: list[str] = []
        for j, txt in enumerate(current_texts):
            if j > 0:
                parts.append(MARKER.format(j))
            parts.append(txt)
        chunks.append(
            Chunk(
                entry_indices=list(current_indices),
                source_text=" ".join(parts),
                marker_count=len(current_indices) - 1,
            )
        )
        current_indices.clear()
        current_texts.clear()

    for i, (entry, text) in enumerate(zip(entries, entry_texts)):
        if not text.strip():
            flush()
            chunks.append(Chunk(entry_indices=[i], source_text="", marker_count=0))
            continue

        force_new = False

        if current_indices:
            prev = entries[current_indices[-1]]
            gap = timecode_to_ms(entry.start) - timecode_to_ms(prev.end)
            if gap >= gap_threshold_ms:
                force_new = True

        current_size = sum(len(t) for t in current_texts)
        if current_size + len(text) > max_chunk_chars and current_indices:
            force_new = True

        if force_new:
            flush()

        current_indices.append(i)
        current_texts.append(text)

    flush()
    return chunks


def detect_style(entry_texts: list[str]) -> str:
    non_empty = [t for t in entry_texts if t.strip()]
    if not non_empty:
        return "mixed"
    avg = sum(len(t) for t in non_empty) / len(non_empty)
    if avg < 35:
        return "short"
    if avg > 75:
        return "long"
    return "mixed"
