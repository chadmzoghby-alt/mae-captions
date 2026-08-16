"""Reject files and text that must never enter the Mae Captions public history."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

FORBIDDEN_EXACT = {
    ".env",
    "CLAUDE.md",
    "HANDOFF.md",
    "config.yaml",
    "glossary.csv",
    "quick-save.bat",
    "quick-save.sh",
}

FORBIDDEN_PARTS = {
    ".claude",
    ".continue",
    ".pi",
    ".pytest_cache",
    ".rpiv",
    "__pycache__",
    "mae_captions.egg-info",
    "node_modules",
    "outputs",
    "target",
    "srt" + "_translator",
}

FORBIDDEN_PREFIXES = (
    ".publication/",
    "docs/plans/",
    "docs/reports/",
    "inputs/",
    "var/",
)

FORBIDDEN_SUFFIXES = (
    ".key",
    ".log",
    ".p12",
    ".pem",
    ".pfx",
    ".pyc",
)

TEXT_SUFFIXES = {
    "",
    ".bat",
    ".cfg",
    ".css",
    ".csv",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsx",
    ".lock",
    ".md",
    ".ps1",
    ".py",
    ".rs",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}

CONTENT_RULES = {
    "OpenAI credential": re.compile(r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}"),
    "Anthropic credential": re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}"),
    "GitHub credential": re.compile(
        r"\b(?:gh[opusr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"
    ),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "literal credential assignment": re.compile(
        r"(?i)\b(?:api[_-]?key|token|secret)\s*[:=]\s*[\"'][^\"'\s]{8,}"
    ),
    "private Windows path": re.compile(r"(?i)\b[A-Z]:\\(?:Users|new-world)\\"),
    "private Unix path": re.compile(r"/(?:Users|home)/[^/\s]+/"),
    "obsolete product identity": re.compile(
        r"(?i)\bsubtitle[\s_-]+(?:edi"
        r"tor|trans"
        r"lator)\b"
        r"|\bsrt[\s_-]+trans"
        r"lator\b"
    ),
}


def _tracked_files(root: Path) -> list[Path]:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
        ],
        check=True,
        capture_output=True,
    )
    return [root / item.decode("utf-8") for item in result.stdout.split(b"\0") if item]


def _path_failures(relative: PurePosixPath) -> list[str]:
    text = relative.as_posix()
    failures: list[str] = []

    if text in FORBIDDEN_EXACT:
        failures.append("forbidden private or local file")
    if any(part in FORBIDDEN_PARTS for part in relative.parts):
        failures.append("forbidden generated, private, input, or output directory")
    if text.startswith(FORBIDDEN_PREFIXES):
        failures.append("forbidden private, runtime, input, or output path")
    if text.lower().endswith(FORBIDDEN_SUFFIXES):
        failures.append("forbidden credential, log, or generated file type")
    if relative.suffix.lower() == ".srt":
        allowed_fixture = (
            text.startswith("tests/fixtures/") and "synthetic" in relative.name.lower()
        )
        if not allowed_fixture:
            failures.append("subtitle files must be named synthetic and live under tests/fixtures")

    return failures


def _content_failures(path: Path) -> list[str]:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return []

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ["text-like file is not readable UTF-8"]

    return [classification for classification, rule in CONTENT_RULES.items() if rule.search(text)]


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    failures: list[tuple[str, str]] = []

    for path in _tracked_files(root):
        relative = PurePosixPath(path.relative_to(root).as_posix())
        for classification in _path_failures(relative):
            failures.append((relative.as_posix(), classification))
        if path.is_file():
            for classification in _content_failures(path):
                failures.append((relative.as_posix(), classification))

    if failures:
        print("Public repository guard failed:", file=sys.stderr)
        for relative, classification in sorted(set(failures)):
            print(f"- {relative}: {classification}", file=sys.stderr)
        return 1

    print("Public repository guard passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
