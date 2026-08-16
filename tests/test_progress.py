import contextlib
import io
import json
import unittest

from mae_captions import progress


class ProgressEventTests(unittest.TestCase):
    def tearDown(self):
        progress.configure(False)

    def test_progress_event_serializes_wire_format_with_event_key(self):
        self.assertTrue(hasattr(progress, "EventType"))
        self.assertTrue(hasattr(progress, "ProgressEvent"))
        EventType = progress.EventType
        ProgressEvent = progress.ProgressEvent
        event = ProgressEvent(EventType.PASS_START, {"pass": 4, "name": "Lexical Review"})

        self.assertEqual(
            json.loads(event.to_json()),
            {"event": "pass:start", "pass": 4, "name": "Lexical Review"},
        )

    def test_emit_accepts_event_type_and_writes_json_line_when_enabled(self):
        self.assertTrue(hasattr(progress, "EventType"))
        EventType = progress.EventType
        progress.configure(True)
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            progress.emit(EventType.LANG_CHUNK, lang="es_LA", chunk=1, total=2)

        self.assertEqual(
            json.loads(output.getvalue()),
            {"event": "lang:chunk", "lang": "es_LA", "chunk": 1, "total": 2},
        )

    def test_emit_is_quiet_when_disabled(self):
        self.assertTrue(hasattr(progress, "EventType"))
        EventType = progress.EventType
        progress.configure(False)
        output = io.StringIO()

        with contextlib.redirect_stdout(output):
            progress.emit(EventType.JOB_DONE, elapsed_ms=12)

        self.assertEqual(output.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
