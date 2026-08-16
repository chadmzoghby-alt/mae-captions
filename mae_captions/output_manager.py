from __future__ import annotations

import json
import shutil
import threading
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


def _json_default(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


class OutputManager:
    def __init__(self, input_path: Path, output_root: Path, skip_existing: bool):
        self._stem = input_path.stem
        self._output_dir = output_root / self._stem
        self._passes_dir = self._output_dir / "passes"
        self._skip_existing = skip_existing
        self._log_lock = threading.Lock()
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._passes_dir.mkdir(parents=True, exist_ok=True)

    def output_dir(self) -> Path:
        return self._output_dir

    def passes_dir(self) -> Path:
        return self._passes_dir

    def final_srt_path(self, code: str) -> Path:
        return self._output_dir / f"{self._stem}.{code}.srt"

    def pass_path(self, pass_num: int, code: str | None, ext: str) -> Path:
        if code:
            return self._passes_dir / f"pass{pass_num}_{code}.{ext}"
        return self._passes_dir / f"pass{pass_num}.{ext}"

    def should_skip(self, code: str) -> bool:
        return self._skip_existing and self.final_srt_path(code).exists()

    def write_json(self, obj: Any, pass_num: int, code: str | None = None) -> None:
        path = self.pass_path(pass_num, code, "json")
        path.write_text(
            json.dumps(obj, default=_json_default, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def finalize_srt(self, code: str) -> Path:
        """Copy the pass-7 SRT from passes/ up to the output root. Returns final path."""
        src = self.pass_path(7, code, "srt")
        dst = self.final_srt_path(code)
        shutil.copy2(src, dst)
        return dst

    def log(self, message: str) -> None:
        log_path = self._passes_dir / "pipeline.log"
        with self._log_lock:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(message + "\n")
