import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from mae_captions.chunker import Chunk
from mae_captions.cli import _prepare_translation_source_chunks, _process_file
from mae_captions.config import Config
from mae_captions.languages import LanguageDef
from mae_captions.output_manager import OutputManager
from mae_captions.providers import claude_prov, openai_prov
from mae_captions.providers.base import BaseProvider


class TranslationSourcePromptTests(unittest.TestCase):
    def test_base_provider_defines_translation_source_method(self):
        self.assertTrue(hasattr(BaseProvider, "prepare_translation_source"))

    def test_translation_source_prompt_allows_semantic_cleanup(self):
        for prompt in (
            claude_prov._TRANSLATION_SOURCE_BASE,
            openai_prov._TRANSLATION_SOURCE_BASE,
        ):
            self.assertIn(
                "Prepare this English subtitle text as a clear source for translation", prompt
            )
            self.assertIn("You may correct grammar", prompt)
            self.assertIn("sentence flow", prompt)
            self.assertIn("Do not add new information", prompt)
            self.assertIn("Keep every marker exactly once", prompt)

    def test_translation_source_prompt_is_distinct_from_lexical_review_prompt(self):
        self.assertNotEqual(claude_prov._TRANSLATION_SOURCE_BASE, claude_prov._REVIEW_BASE)
        self.assertNotEqual(openai_prov._TRANSLATION_SOURCE_BASE, openai_prov._REVIEW_BASE)


class FakeSemanticProvider:
    name = "fake"

    def __init__(self):
        self.calls = []

    def prepare_translation_source(self, text, glossary_terms="", source_context=""):
        self.calls.append((text, glossary_terms, source_context))
        return text.replace("I'm in a small", "In a small way, I am")


class MarkerRetryProvider:
    name = "fake"

    def __init__(self):
        self.calls = 0

    def prepare_translation_source(self, text, glossary_terms="", source_context=""):
        self.calls += 1
        if self.calls == 1:
            return "alpha beta"
        return "alpha <<1>> beta"


class TranslationSourceChunkTests(unittest.TestCase):
    def test_prepare_translation_source_chunks_mutates_only_translation_chunks(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "movie.srt"
            input_path.write_text("", encoding="utf-8")
            om = OutputManager(input_path, Path(tmp) / "outputs", skip_existing=False)
            provider = FakeSemanticProvider()
            chunks = [Chunk(entry_indices=[0], source_text="I'm in a small", marker_count=0)]

            _prepare_translation_source_chunks(
                chunks,
                provider,
                parallel=1,
                om=om,
                glossary_terms="",
                source_context="test lecture",
            )

            self.assertEqual(chunks[0].source_text, "In a small way, I am")
            self.assertEqual(provider.calls[0][2], "test lecture")

    def test_prepare_translation_source_chunks_retries_marker_mismatches(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "movie.srt"
            input_path.write_text("", encoding="utf-8")
            om = OutputManager(input_path, Path(tmp) / "outputs", skip_existing=False)
            provider = MarkerRetryProvider()
            chunks = [Chunk(entry_indices=[0, 1], source_text="alpha <<1>> beta", marker_count=1)]

            _prepare_translation_source_chunks(
                chunks,
                provider,
                parallel=1,
                om=om,
            )

            self.assertEqual(provider.calls, 2)
            self.assertEqual(chunks[0].source_text, "alpha <<1>> beta")


class FakePipelineProvider:
    name = "fake"

    def __init__(self):
        self.translate_calls = []
        self.prepare_calls = 0

    def review(self, text, glossary_terms="", source_context=""):
        return text.split("\n", 1)[1]

    def prepare_translation_source(self, text, glossary_terms="", source_context=""):
        self.prepare_calls += 1
        source = text.split("\n", 1)[1]
        return source.replace("I'm in a small", "In a small way, I am")

    def translate(self, text, source_lang, target_lang, preceding_context=""):
        self.translate_calls.append(text)
        return "translated"


class TranslationSourcePipelineTests(unittest.TestCase):
    def test_process_file_uses_semantic_chunks_for_translation_not_en_us(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "movie.srt"
            input_path.write_text(
                "1\n00:00:00,000 --> 00:00:01,000\n<b>I'm in a small</b>\n",
                encoding="utf-8",
            )
            output_root = root / "outputs"
            cfg = Config()
            cfg.source_context = "test lecture"
            provider = FakePipelineProvider()
            args = SimpleNamespace(parallel=1, parallel_languages=1)

            ok = _process_file(
                input_path=input_path,
                file_idx=0,
                file_total=1,
                args=args,
                cfg=cfg,
                target_langs=[LanguageDef("es_LA", "Spanish", 42)],
                source_lang="English",
                provider=provider,
                model_display="fake-model",
                glossary_note="",
                glossary_terms="",
                output_root=output_root,
                skip_existing=False,
            )

            self.assertTrue(ok)
            output_dir = output_root / "movie"
            en_us = (output_dir / "movie.en_US.srt").read_text(encoding="utf-8")
            self.assertIn("<b>I'm in a small</b>", en_us)
            self.assertNotIn("In a small way, I am", en_us)
            self.assertTrue((output_dir / "passes" / "pass4_translation_source.json").exists())
            self.assertTrue((output_dir / "passes" / "pass4_translation_source.srt").exists())
            self.assertFalse((output_dir / "movie.translation_source.srt").exists())
            self.assertIn("In a small way, I am", provider.translate_calls[0])

    def test_process_file_skips_semantic_source_when_no_translation_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "movie.srt"
            input_path.write_text(
                "1\n00:00:00,000 --> 00:00:01,000\nI'm in a small\n",
                encoding="utf-8",
            )
            output_root = root / "outputs"
            provider = FakePipelineProvider()
            args = SimpleNamespace(parallel=1, parallel_languages=1)

            ok = _process_file(
                input_path=input_path,
                file_idx=0,
                file_total=1,
                args=args,
                cfg=Config(),
                target_langs=[],
                source_lang="English",
                provider=provider,
                model_display="fake-model",
                glossary_note="",
                glossary_terms="",
                output_root=output_root,
                skip_existing=False,
            )

            self.assertTrue(ok)
            self.assertEqual(provider.prepare_calls, 0)
            self.assertFalse(
                (output_root / "movie" / "passes" / "pass4_translation_source.json").exists()
            )


if __name__ == "__main__":
    unittest.main()
