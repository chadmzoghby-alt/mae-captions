import unittest

from mae_captions.srt_parser import Entry
from mae_captions.text_processor import _strip_tags, restore_tags, strip_and_index


class TextProcessorTagTests(unittest.TestCase):
    def test_strip_tags_records_simple_and_self_closing_tags_in_order(self):
        clean, tags = _strip_tags("<i>Hello</i><br/><b>world</b>", 0)

        self.assertEqual(clean, "Helloworld")
        self.assertEqual(
            [(tag.char_offset, tag.tag) for tag in tags],
            [(0, "<i>"), (5, "</i>"), (5, "<br/>"), (5, "<b>"), (10, "</b>")],
        )

    def test_strip_tags_preserves_attributes_and_offsets(self):
        clean, tags = _strip_tags('text <font color="red">styled</font> more text', 0)

        self.assertEqual(clean, "text styled more text")
        self.assertEqual(tags[0].char_offset, 5)
        self.assertEqual(tags[0].tag, '<font color="red">')

    def test_strip_tags_preserves_entities_as_clean_text(self):
        clean, tags = _strip_tags("Fish &amp; chips", 0)

        self.assertEqual(clean, "Fish &amp; chips")
        self.assertEqual(tags, [])

    def test_strip_tags_handles_attribute_values_containing_greater_than(self):
        clean, tags = _strip_tags('<a title="a > b" href="/page">link</a>', 0)

        self.assertEqual(clean, "link")
        self.assertEqual(tags[0].tag, '<a title="a > b" href="/page">')
        self.assertEqual(restore_tags(clean, tags, 0), '<a title="a > b" href="/page">link</a>')

    def test_strip_and_restore_preserves_nested_tags(self):
        entries = [Entry(1, "00:00:00,000", "00:00:01,000", ["<b><i>nested</i></b>"])]

        corpus = strip_and_index(entries)

        self.assertEqual(corpus.entry_texts, ["nested"])
        self.assertEqual(
            [tag.tag for tag in corpus.tag_records],
            ["<b>", "<i>", "</i>", "</b>"],
        )
        self.assertEqual(restore_tags("nested", corpus.tag_records, 0), "<b><i>nested</i></b>")


if __name__ == "__main__":
    unittest.main()
