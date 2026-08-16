from dataclasses import dataclass
from html.parser import HTMLParser

from .srt_parser import Entry


@dataclass
class TagRecord:
    entry_index: int
    char_offset: int
    tag: str


@dataclass
class ProcessedCorpus:
    entry_texts: list[str]
    tag_records: list[TagRecord]
    position_map: list[tuple[int, int, int]]


def strip_and_index(entries: list[Entry]) -> ProcessedCorpus:
    entry_texts: list[str] = []
    tag_records: list[TagRecord] = []
    position_map: list[tuple[int, int, int]] = []
    pos = 0

    for i, entry in enumerate(entries):
        raw_text = " ".join(entry.lines)
        clean, tags = _strip_tags(raw_text, i)
        entry_texts.append(clean)
        tag_records.extend(tags)
        position_map.append((i, pos, pos + len(clean)))
        pos += len(clean) + 1

    return ProcessedCorpus(
        entry_texts=entry_texts,
        tag_records=tag_records,
        position_map=position_map,
    )


class _TagStripper(HTMLParser):
    def __init__(self, entry_idx: int):
        super().__init__(convert_charrefs=False)
        self.entry_idx = entry_idx
        self._offset = 0
        self.clean_chars: list[str] = []
        self.tags: list[TagRecord] = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(
            TagRecord(
                entry_index=self.entry_idx,
                char_offset=self._offset,
                tag=self.get_starttag_text(),
            )
        )

    def handle_endtag(self, tag):
        self.tags.append(
            TagRecord(
                entry_index=self.entry_idx,
                char_offset=self._offset,
                tag=f"</{tag}>",
            )
        )

    def handle_startendtag(self, tag, attrs):
        self.tags.append(
            TagRecord(
                entry_index=self.entry_idx,
                char_offset=self._offset,
                tag=self.get_starttag_text(),
            )
        )

    def handle_data(self, data):
        self.clean_chars.append(data)
        self._offset += len(data)

    def handle_entityref(self, name):
        entity = f"&{name};"
        self.clean_chars.append(entity)
        self._offset += len(entity)

    def handle_charref(self, name):
        charref = f"&#{name};"
        self.clean_chars.append(charref)
        self._offset += len(charref)


def _strip_tags(text: str, entry_idx: int) -> tuple[str, list[TagRecord]]:
    stripper = _TagStripper(entry_idx)
    stripper.feed(text)
    stripper.close()
    return "".join(stripper.clean_chars), stripper.tags


def restore_tags(text: str, tag_records: list[TagRecord], entry_idx: int) -> str:
    relevant = sorted(
        [t for t in tag_records if t.entry_index == entry_idx],
        key=lambda t: t.char_offset,
    )
    if not relevant:
        return text

    # Re-insert each tag at its original char offset, adjusting for previously
    # inserted tags shifting the string right.
    shift = 0
    for tag in relevant:
        pos = min(tag.char_offset + shift, len(text))
        text = text[:pos] + tag.tag + text[pos:]
        shift += len(tag.tag)

    return text
