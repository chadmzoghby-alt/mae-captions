import inspect
import unittest

from mae_captions.chunker import Chunk
from mae_captions.reassembler import _merge_short_entries, reassemble
from mae_captions.srt_parser import Entry
from mae_captions.text_processor import strip_and_index


def entry(index: int, start: str, end: str, text: str) -> Entry:
    return Entry(index, start, end, [text])


class ReassemblerTests(unittest.TestCase):
    def test_exact_marker_match_assigns_segments_to_entries(self):
        entries = [
            entry(1, "00:00:00,000", "00:00:01,000", "alpha"),
            entry(2, "00:00:01,000", "00:00:02,000", "beta"),
        ]
        corpus = strip_and_index(entries)
        chunks = [Chunk(entry_indices=[0, 1], source_text="alpha <<1>> beta", marker_count=1)]

        result, warnings = reassemble(entries, chunks, ["uno <<1>> dos"], corpus)

        self.assertEqual(warnings, [])
        self.assertEqual([e.lines for e in result], [["uno"], ["dos"]])

    def test_missing_marker_uses_proportional_fallback(self):
        entries = [
            entry(1, "00:00:00,000", "00:00:01,000", "alpha"),
            entry(2, "00:00:01,000", "00:00:02,000", "beta"),
        ]
        corpus = strip_and_index(entries)
        chunks = [Chunk(entry_indices=[0, 1], source_text="alpha <<1>> beta", marker_count=1)]

        result, warnings = reassemble(entries, chunks, ["uno dos"], corpus)

        self.assertEqual(len(warnings), 1)
        self.assertIn("proportional fallback used", warnings[0])
        self.assertEqual([e.lines for e in result], [["uno"], ["dos"]])

    def test_extra_marker_uses_proportional_fallback(self):
        entries = [
            entry(1, "00:00:00,000", "00:00:01,000", "alpha"),
            entry(2, "00:00:01,000", "00:00:02,000", "beta"),
        ]
        corpus = strip_and_index(entries)
        chunks = [Chunk(entry_indices=[0, 1], source_text="alpha <<1>> beta", marker_count=1)]

        result, warnings = reassemble(entries, chunks, ["uno <<1>> dos <<2>> tres"], corpus)

        self.assertEqual(len(warnings), 1)
        self.assertEqual(" ".join(line[0] for line in [e.lines for e in result]), "uno dos tres")

    def test_long_entry_splits_with_interpolated_timecodes(self):
        entries = [entry(1, "00:00:00,000", "00:00:04,000", "placeholder")]
        corpus = strip_and_index(entries)
        chunks = [Chunk(entry_indices=[0], source_text="placeholder", marker_count=0)]

        result, warnings = reassemble(
            entries,
            chunks,
            ["one two three four"],
            corpus,
            max_line_chars=8,
        )

        self.assertEqual(warnings, [])
        self.assertEqual([e.lines for e in result], [["one two"], ["three"], ["four"]])
        self.assertEqual(
            [(e.start, e.end) for e in result],
            [
                ("00:00:00,000", "00:00:01,333"),
                ("00:00:01,333", "00:00:02,666"),
                ("00:00:02,666", "00:00:04,000"),
            ],
        )

    def test_short_entries_merge_with_neighbour(self):
        entries = [
            entry(1, "00:00:00,000", "00:00:01,000", "aa"),
            entry(2, "00:00:01,000", "00:00:02,000", "bb"),
        ]
        corpus = strip_and_index(entries)
        chunks = [
            Chunk(entry_indices=[0], source_text="aa", marker_count=0),
            Chunk(entry_indices=[1], source_text="bb", marker_count=0),
        ]

        result, warnings = reassemble(
            entries,
            chunks,
            ["aa", "bb"],
            corpus,
            max_line_chars=10,
            min_entry_chars=5,
        )

        self.assertEqual(warnings, [])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].lines, ["aa bb"])
        self.assertEqual((result[0].start, result[0].end), ("00:00:00,000", "00:00:02,000"))

    def test_preserve_entry_boundaries_skips_split_and_merge(self):
        entries = [
            entry(1, "00:00:00,000", "00:00:01,000", "aa"),
            entry(2, "00:00:01,000", "00:00:02,000", "long text"),
        ]
        corpus = strip_and_index(entries)
        chunks = [
            Chunk(entry_indices=[0], source_text="aa", marker_count=0),
            Chunk(entry_indices=[1], source_text="long text", marker_count=0),
        ]

        result, warnings = reassemble(
            entries,
            chunks,
            ["aa", "long text"],
            corpus,
            max_line_chars=4,
            min_entry_chars=10,
            preserve_entry_boundaries=True,
        )

        self.assertEqual(warnings, [])
        self.assertEqual([e.lines for e in result], [["aa"], ["long text"]])

    def test_merge_short_entries_refactor_does_not_mutate_with_pop(self):
        source = inspect.getsource(_merge_short_entries)

        self.assertNotIn(".pop(", source)


if __name__ == "__main__":
    unittest.main()
