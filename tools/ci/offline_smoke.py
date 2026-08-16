"""Run Mae Captions' dry-run path while denying all network access."""

from __future__ import annotations

import os
import socket
import sys
from pathlib import Path
from unittest import mock


class NetworkAccessError(RuntimeError):
    """Raised when an offline smoke test attempts network access."""


def _block_network(*_args: object, **_kwargs: object) -> None:
    raise NetworkAccessError("network access is forbidden during the CI dry run")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: offline_smoke.py PATH_TO_SYNTHETIC_SRT", file=sys.stderr)
        return 2

    fixture = Path(sys.argv[1]).resolve()
    if not fixture.is_file():
        print(f"synthetic fixture not found: {fixture}", file=sys.stderr)
        return 2

    for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
        os.environ.pop(name, None)

    repository_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repository_root))

    from mae_captions.cli import main as cli_main

    with (
        mock.patch.object(socket.socket, "connect", _block_network),
        mock.patch.object(socket, "create_connection", _block_network),
        mock.patch.object(socket, "getaddrinfo", _block_network),
    ):
        result = cli_main([str(fixture), "--preset", "top5", "--dry-run"])

    return result if isinstance(result, int) else 0


if __name__ == "__main__":
    raise SystemExit(main())
