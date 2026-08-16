import inspect
import unittest

from mae_captions.chunker import chunk_entries
from mae_captions.srt_parser import Entry


def entry(index: int, start: str, end: str, text: str) -> Entry:
    return Entry(index, start, end, [text])


class ChunkerTests(unittest.TestCase):
    def test_single_entry_produces_one_chunk_with_no_markers(self):
        entries = [entry(1, "00:00:00,000", "00:00:01,000", "hello")]

        chunks = chunk_entries(entries, ["hello"], max_chunk_chars=100, gap_threshold_ms=1200)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].entry_indices, [0])
        self.assertEqual(chunks[0].source_text, "hello")
        self.assertEqual(chunks[0].marker_count, 0)

    def test_close_entries_share_chunk_with_marker(self):
        entries = [
            entry(1, "00:00:00,000", "00:00:01,000", "hello"),
            entry(2, "00:00:01,500", "00:00:02,000", "world"),
        ]

        chunks = chunk_entries(
            entries, ["hello", "world"], max_chunk_chars=100, gap_threshold_ms=1200
        )

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].entry_indices, [0, 1])
        self.assertEqual(chunks[0].source_text, "hello <<1>> world")
        self.assertEqual(chunks[0].marker_count, 1)

    def test_large_gap_forces_new_chunk(self):
        entries = [
            entry(1, "00:00:00,000", "00:00:01,000", "hello"),
            entry(2, "00:00:03,000", "00:00:04,000", "world"),
        ]

        chunks = chunk_entries(
            entries, ["hello", "world"], max_chunk_chars=100, gap_threshold_ms=1200
        )

        self.assertEqual([chunk.entry_indices for chunk in chunks], [[0], [1]])
        self.assertEqual([chunk.marker_count for chunk in chunks], [0, 0])

    def test_max_chunk_chars_forces_new_chunk_before_entry_that_exceeds_cap(self):
        entries = [
            entry(1, "00:00:00,000", "00:00:01,000", "alpha"),
            entry(2, "00:00:01,100", "00:00:02,000", "beta"),
        ]

        chunks = chunk_entries(entries, ["alpha", "beta"], max_chunk_chars=8, gap_threshold_ms=1200)

        self.assertEqual([chunk.entry_indices for chunk in chunks], [[0], [1]])

    def test_empty_entries_are_pass_through_chunks(self):
        entries = [
            entry(1, "00:00:00,000", "00:00:01,000", "alpha"),
            entry(2, "00:00:01,100", "00:00:02,000", ""),
            entry(3, "00:00:02,100", "00:00:03,000", "omega"),
        ]

        chunks = chunk_entries(
            entries, ["alpha", "", "omega"], max_chunk_chars=100, gap_threshold_ms=1200
        )

        self.assertEqual([chunk.entry_indices for chunk in chunks], [[0], [1], [2]])
        self.assertEqual(chunks[1].source_text, "")
        self.assertEqual(chunks[1].marker_count, 0)

    def test_chunk_entries_requires_explicit_config_values(self):
        signature = inspect.signature(chunk_entries)

        self.assertEqual(signature.parameters["max_chunk_chars"].default, inspect.Parameter.empty)
        self.assertEqual(signature.parameters["gap_threshold_ms"].default, inspect.Parameter.empty)


if __name__ == "__main__":
    unittest.main()
