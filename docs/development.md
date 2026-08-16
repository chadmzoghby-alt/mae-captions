# Developing Mae Captions

The public alpha accepts focused bug reports and feature requests, but not external patches. Read [CONTRIBUTING.md](../CONTRIBUTING.md), [SECURITY.md](../SECURITY.md), and [SUPPORT.md](../SUPPORT.md) before reporting a problem.

## Install test dependencies

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-ci.txt
```

## Run the local checks

```bash
python -m compileall -q mae_captions tests tools/ci
python -m ruff check mae_captions tests tools/ci
python -m ruff format --check mae_captions tests tools/ci
python -m unittest discover -s tests -v
python tools/ci/offline_smoke.py tests/fixtures/synthetic.srt
python tools/ci/repository_guard.py .
```

Routine tests use original synthetic text. Do not make live Anthropic, OpenAI, or other paid-provider calls in tests.

I developed and locally validated the alpha on Windows. The repository includes CI definitions for Linux, Windows, and macOS; cross-platform public results can be recorded after the first public CI run.
