import unittest

from mae_captions.chunker import Chunk
from mae_captions.providers import claude_prov, openai_prov
from mae_captions.reassembler import reassemble
from mae_captions.srt_parser import Entry
from mae_captions.text_processor import restore_tags, strip_and_index


class LexicalReviewTests(unittest.TestCase):
    def test_review_prompt_forbids_paraphrasing(self):
        for prompt in (claude_prov._REVIEW_BASE, openai_prov._REVIEW_BASE):
            self.assertIn("Do not paraphrase", prompt)
            self.assertIn("Do not replace words with synonyms", prompt)
            self.assertIn("Do not expand contractions", prompt)
            self.assertNotIn("unnatural phrasing", prompt)
            self.assertNotIn("natural spoken flow", prompt)

    def test_reassemble_can_preserve_original_entry_boundaries(self):
        entries = [
            Entry(1, "00:00:00,000", "00:00:01,000", ["short"]),
            Entry(2, "00:00:01,000", "00:00:02,000", ["tiny"]),
        ]
        corpus = strip_and_index(entries)
        chunks = [Chunk(entry_indices=[0, 1], source_text="short <<1>> tiny", marker_count=1)]

        reviewed, warnings = reassemble(
            entries,
            chunks,
            ["short <<1>> tiny"],
            corpus,
            max_line_chars=3,
            min_entry_chars=20,
            preserve_entry_boundaries=True,
        )

        self.assertEqual(warnings, [])
        self.assertEqual(len(reviewed), 2)
        self.assertEqual(reviewed[0].lines, ["short"])
        self.assertEqual(reviewed[1].lines, ["tiny"])

    def test_strip_and_restore_preserves_bold_tags(self):
        entries = [Entry(1, "00:00:00,000", "00:00:01,000", ["<b>Hello</b>"])]

        corpus = strip_and_index(entries)

        self.assertEqual(corpus.entry_texts, ["Hello"])
        self.assertEqual(restore_tags("Hello", corpus.tag_records, 0), "<b>Hello</b>")


if __name__ == "__main__":
    unittest.main()
