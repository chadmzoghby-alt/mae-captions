from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

_enabled: bool = False
_emit_lock: threading.Lock | None = None


class EventType(Enum):
    JOB_START = "job:start"
    JOB_DONE = "job:done"
    FILE_START = "file:start"
    FILE_DONE = "file:done"
    PASS_START = "pass:start"
    PASS_CHUNK = "pass:chunk"
    PASS_DONE = "pass:done"
    LANG_START = "lang:start"
    LANG_CHUNK = "lang:chunk"
    LANG_DONE = "lang:done"
    LANG_FAILED = "lang:failed"
    FATAL_ERROR = "job:fatal"


@dataclass(frozen=True)
class ProgressEvent:
    event: EventType
    data: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps({"event": self.event.value, **self.data}, ensure_ascii=False)


def configure(enabled: bool) -> None:
    """Enable or disable progress event emission."""
    global _enabled, _emit_lock
    _enabled = enabled
    _emit_lock = threading.Lock() if enabled else None


def emit(event_type: EventType, **payload: Any) -> None:
    """Print a JSON progress event to stdout when enabled."""
    if not _enabled or _emit_lock is None:
        return
    event = ProgressEvent(event=event_type, data=payload)
    with _emit_lock:
        print(event.to_json(), flush=True)
