import re

from .chunker import Chunk
from .srt_parser import Entry, ms_to_timecode, timecode_to_ms
from .text_processor import ProcessedCorpus, restore_tags

MARKER_RE = re.compile(r"<<\d+>>")


def reassemble(
    entries: list[Entry],
    chunks: list[Chunk],
    translations: list[str],
    corpus: ProcessedCorpus,
    max_line_chars: int = 42,
    min_entry_chars: int = 0,
    preserve_entry_boundaries: bool = False,
) -> tuple[list[Entry], list[str]]:
    """Returns (result_entries, fallback_warnings)."""
    result = [Entry(index=e.index, start=e.start, end=e.end, lines=list(e.lines)) for e in entries]

    warnings: list[str] = []

    for chunk, translated in zip(chunks, translations):
        if not chunk.entry_indices:
            continue

        if not chunk.source_text.strip() or not translated.strip():
            continue

        if len(chunk.entry_indices) == 1:
            idx = chunk.entry_indices[0]
            text = restore_tags(translated.strip(), corpus.tag_records, idx)
            result[idx].lines = [text]
            continue

        segments = MARKER_RE.split(translated)
        segments = [s.strip() for s in segments]

        if len(segments) == len(chunk.entry_indices):
            for seg, idx in zip(segments, chunk.entry_indices):
                text = restore_tags(seg, corpus.tag_records, idx)
                result[idx].lines = [text]
        else:
            warnings.append(
                f"chunk entries {chunk.entry_indices[0]}-{chunk.entry_indices[-1]}: "
                f"expected {chunk.marker_count} markers, got {len(segments) - 1} "
                f"— proportional fallback used"
            )
            _proportional_assign(result, chunk, translated, corpus)

    if preserve_entry_boundaries:
        return result, warnings

    # Split any entries whose text exceeds max_line_chars into additional entries
    # with proportionally interpolated timecodes.
    final: list[Entry] = []
    for entry in result:
        text = " ".join(entry.lines).strip()
        if not text or len(text) <= max_line_chars:
            final.append(entry)
        else:
            final.extend(_split_entry(entry, text, max_line_chars, min_entry_chars))

    # Merge any entries still below min_entry_chars across source boundaries.
    if min_entry_chars > 0 and len(final) > 1:
        final = _merge_short_entries(final, max_line_chars, min_entry_chars)

    return final, warnings


def _proportional_assign(
    result: list[Entry],
    chunk: Chunk,
    translated: str,
    corpus: ProcessedCorpus,
) -> None:
    clean = " ".join(MARKER_RE.sub("", translated).split())
    total_src = sum(len(corpus.entry_texts[i]) for i in chunk.entry_indices)
    if total_src == 0:
        return

    offset = 0
    for k, idx in enumerate(chunk.entry_indices):
        src_len = len(corpus.entry_texts[idx])
        proportion = src_len / total_src
        char_count = round(proportion * len(clean))

        if k == len(chunk.entry_indices) - 1:
            segment = clean[offset:].strip()
        else:
            target = min(offset + char_count, len(clean))
            end = _nearest_word_boundary(clean, offset, target)
            segment = clean[offset:end].strip()
            offset = end
            while offset < len(clean) and clean[offset].isspace():
                offset += 1

        text = restore_tags(segment, corpus.tag_records, idx)
        result[idx].lines = [text]


def _nearest_word_boundary(text: str, start: int, target: int) -> int:
    if target >= len(text):
        previous = text.rfind(" ", start, len(text))
        return previous if previous > start else len(text)
    if text[target].isspace():
        return target

    previous = text.rfind(" ", start, target)
    next_space = text.find(" ", target)
    if previous <= start:
        return next_space if next_space != -1 else len(text)
    if next_space == -1:
        return previous
    return previous if target - previous <= next_space - target else next_space


def _split_text(text: str, max_chars: int, min_chars: int = 0) -> list[str]:
    """Split text into segments of at most max_chars at word boundaries,
    then merge any segment shorter than min_chars into its neighbour."""
    words = text.split()
    segments: list[str] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        if current and current_len + 1 + len(word) > max_chars:
            segments.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current_len = current_len + (1 if current else 0) + len(word)
            current.append(word)

    if current:
        segments.append(" ".join(current))

    if min_chars > 0 and len(segments) > 1:
        segments = _merge_short_segments(segments, max_chars, min_chars)

    return segments or [text]


def _merge_short_segments(segments: list[str], max_chars: int, min_chars: int) -> list[str]:
    """Merge any segment shorter than min_chars into an adjacent neighbour."""
    result = list(segments)
    i = 0
    while i < len(result):
        if len(result[i]) < min_chars and len(result) > 1:
            # Prefer merging with the previous segment if it fits.
            if i > 0 and len(result[i - 1]) + 1 + len(result[i]) <= max_chars:
                result[i - 1] = result[i - 1] + " " + result[i]
                result.pop(i)
            # Otherwise try the next segment.
            elif i < len(result) - 1 and len(result[i]) + 1 + len(result[i + 1]) <= max_chars:
                result[i + 1] = result[i] + " " + result[i + 1]
                result.pop(i)
            else:
                i += 1
        else:
            i += 1
    return result


def _merge_short_entries(entries: list[Entry], max_chars: int, min_chars: int) -> list[Entry]:
    """Merge consecutive entries whose text is shorter than min_chars into a neighbour."""
    result: list[Entry] = []
    i = 0
    while i < len(entries):
        entry = entries[i]
        text = " ".join(entry.lines).strip()
        if len(text) < min_chars and len(result) + (len(entries) - i) > 1:
            if result:
                prev_text = " ".join(result[-1].lines).strip()
                merged = f"{prev_text} {text}".strip()
                if len(merged) <= max_chars:
                    result[-1] = Entry(
                        index=result[-1].index,
                        start=result[-1].start,
                        end=entry.end,
                        lines=[merged],
                    )
                    i += 1
                    continue

            if i + 1 < len(entries):
                next_entry = entries[i + 1]
                next_text = " ".join(next_entry.lines).strip()
                merged = f"{text} {next_text}".strip()
                if len(merged) <= max_chars:
                    result.append(
                        Entry(
                            index=entry.index,
                            start=entry.start,
                            end=next_entry.end,
                            lines=[merged],
                        )
                    )
                    i += 2
                    continue
        result.append(entry)
        i += 1
    return result


def _split_entry(entry: Entry, text: str, max_chars: int, min_chars: int = 0) -> list[Entry]:
    """Split one entry into multiple entries with proportionally interpolated timecodes."""
    segments = _split_text(text, max_chars, min_chars)
    if len(segments) == 1:
        return [Entry(entry.index, entry.start, entry.end, [segments[0]])]

    start_ms = timecode_to_ms(entry.start)
    end_ms = timecode_to_ms(entry.end)
    duration = end_ms - start_ms
    n = len(segments)

    result: list[Entry] = []
    for i, seg in enumerate(segments):
        seg_start = start_ms + (duration * i // n)
        seg_end = start_ms + (duration * (i + 1) // n)
        result.append(
            Entry(
                index=entry.index,
                start=ms_to_timecode(seg_start),
                end=ms_to_timecode(seg_end),
                lines=[seg],
            )
        )
    return result
