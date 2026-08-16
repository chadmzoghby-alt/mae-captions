# Mae Captions

Mae Captions is a Python command-line application for preparing, reviewing, and translating SubRip (`.srt`) caption files while preserving their timing structure.

This repository currently publishes the CLI only. Version `0.1.0` is an alpha source-available release: there are no desktop installers, signed binaries, or automatic updates yet.

## What it does

- Parses SRT files while retaining timecodes and formatting anchors.
- Prepares a reviewed English caption track before downstream translations.
- Translates to one or more target languages through Anthropic, OpenAI, or a local OpenAI-compatible LM Studio server.
- Writes intermediate passes, final SRT files, and a pipeline log beneath the configured output directory.
- Offers a fully offline `--dry-run` path for parsing and chunk inspection.

## Requirements

- Python 3.12 or newer
- User-supplied provider access for Anthropic or OpenAI translations
- Optional: a locally running LM Studio OpenAI-compatible server

Provider credentials and provider usage charges belong to the user. Mae Captions is not affiliated with Anthropic, OpenAI, or LM Studio.

## Install from source

```bash
git clone https://github.com/chadmzoghby-alt/mae-captions.git
cd mae-captions
python -m venv .venv
```

Activate the environment using the command appropriate for your shell, then install:

```bash
python -m pip install .
```

Confirm the CLI is available:

```bash
mae-captions --version
mae-captions --help
```

## Configure

Copy `config.example.yaml` to `config.yaml` if you want persistent non-secret preferences. Do not put credentials in configuration files or command arguments.

For a hosted provider, expose the relevant credential to the Mae Captions process through your operating system or secret manager:

- `ANTHROPIC_API_KEY` for Anthropic
- `OPENAI_API_KEY` for OpenAI

For local processing, start LM Studio's OpenAI-compatible server and select it explicitly:

```bash
mae-captions input.srt --targets de_DE --provider lmstudio --base-url http://localhost:1234/v1
```

## Use

Inspect an SRT without making a provider call:

```bash
mae-captions input.srt --preset top5 --dry-run
```

Translate with a hosted provider:

```bash
mae-captions input.srt --targets de_DE fr_FR --provider openai --model YOUR_MODEL_NAME
```

When no input path is supplied, Mae Captions looks for `.srt` files in `./inputs`. By default, results and `pipeline.log` are written beneath `./outputs`; use `--output-root` or the example configuration to choose another location.

The CLI accepts a glossary CSV with `term,translation` pairs through `--glossary PATH`.

## Privacy and safety

Hosted providers receive caption text when selected. The local dry run makes no network requests, and LM Studio can keep processing local when its server and models are local. Read [PRIVACY.md](PRIVACY.md) before processing sensitive material.

Routine tests use original synthetic text and block network access during the CLI smoke test. Never add real caption files, credentials, output folders, or logs to this repository.

## Development

Install the test tools:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-ci.txt
```

Run the same local checks used by CI:

```bash
python -m compileall -q mae_captions tests tools/ci
python -m ruff check mae_captions tests tools/ci
python -m ruff format --check mae_captions tests tools/ci
python -m unittest discover -s tests -v
python tools/ci/offline_smoke.py tests/fixtures/synthetic.srt
python tools/ci/repository_guard.py .
```

See [LICENSING.md](LICENSING.md), [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and [SUPPORT.md](SUPPORT.md) before using Mae Captions commercially or opening a contribution or report.

## Licensing

Mae Captions is source-available under the [PolyForm Noncommercial License 1.0.0](LICENSE), with a narrow [Independent Freelancer Exception](FREELANCER_EXCEPTION.md): one independent freelancer may personally use an unmodified official copy to produce static deliverables for clients.

Commercial or business use by companies, employers, agencies, partnerships, or teams requires a separate written commercial license, except for the single-person business vehicle allowed by the Freelancer Exception. Operating Mae Captions as a hosted service or providing hosted access to it, embedded uses, commercial redistribution, and commercial use of modified versions also require a commercial license. The base license continues to permit genuine noncommercial purposes and the qualifying organizations it lists. Read the [Licensing Guide](LICENSING.md) before relying on the freelancer permission.

The software is not offered under an OSI-approved open-source license. Direct dependencies remain governed by their own licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Project names and logos are governed separately by [TRADEMARKS.md](TRADEMARKS.md).
