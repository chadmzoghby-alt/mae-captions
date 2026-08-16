# Mae Captions — Local LLM SRT Translation Tool

**Translate SRT subtitles with a local LLM running on your own computer.**

Mae Captions is a small Python command-line tool for reviewing and translating SubRip (`.srt`) subtitle files with large language models.

I built Mae Captions as a Windows user with [LM Studio](https://lmstudio.ai/) in mind. The local-first setup connects Mae Captions to an OpenAI-compatible server on your own computer, so subtitle translation requests can stay between the CLI and your local model instead of being sent to a hosted AI provider.

If you prefer a hosted model, Mae Captions can also use OpenAI or Anthropic.

> [!IMPORTANT]
> Mae Captions `0.1.0` is an alpha command-line application. There is no desktop installer, graphical interface, signed executable, or automatic updater yet.

> [!NOTE]
> Mae Captions is source-available, not open source. Noncommercial use and a narrow solo-freelancer exception are available, but most company, team, hosted, embedded, or other commercial use requires a separate license. Read [Licensing](#licensing) before relying on the software commercially.

The current alpha is designed for **English-language source subtitles**. Its review and translation-source preparation prompts assume English, even when `--source auto` is used later in translation. Do not rely on this version to process non-English source captions correctly.

## Why I made Mae Captions

Traditional subtitle translation is awkward because subtitles are not ordinary blocks of text. They contain:

- dialogue split across many caption entries;
- timecodes and structural information that the language model should not rewrite;
- sentences that continue across subtitle boundaries;
- names and terminology that should stay consistent; and
- occasional transcription, punctuation, or wording problems in the source captions.

Large language models can understand the surrounding language and context, but they should not be responsible for parsing and rebuilding the subtitle format.

That separation is the central idea behind Mae Captions: **the model handles the language; Mae Captions handles the subtitle structure.**

```text
your .srt file
      |
      v
 Mae Captions
      |
      v
 local LLM
      |
      v
translated .srt
```

Mae Captions parses the file, removes structural noise from the text sent to the model, groups related caption entries into manageable chunks, and then deterministically rebuilds normal SRT output. The LLM never sees the timecodes.

## Local-first subtitle translation

The setup I designed around uses a local model through [LM Studio's OpenAI-compatible API](https://lmstudio.ai/docs/developer/openai-compat):

```text
Mae Captions -> http://localhost:1234/v1 -> your local LLM
```

This local AI subtitle workflow can be useful when:

- you do not want Mae Captions sending subtitle text to OpenAI or Anthropic;
- you have a GPU or computer capable of running a suitable local language model;
- you want to translate a large amount of material without per-token provider charges;
- you want to compare Llama, Qwen, Mistral, Gemma, or other local models; or
- you prefer self-hosted tools that can run offline after the software, dependencies, LM Studio, and a model have been downloaded.

Mae Captions does not bundle an LLM or choose one for you. You download and run the model in LM Studio. Translation quality, speed, memory use, and supported languages depend on that model and your hardware.

“Local” here means Mae Captions is pointed at a model server you control. Keep the server bound to `localhost` if you do not intend to expose it to other devices, and review LM Studio's own settings and privacy behavior separately.

## What Mae Captions does

Mae Captions:

- reads standard SubRip (`.srt`) subtitle files with encoding detection;
- keeps timecodes away from the LLM and reconstructs subtitle structure deterministically;
- preserves and restores common inline formatting such as italics and bold text;
- groups caption entries so the model can understand sentences across cue boundaries;
- creates a conservative AI review-pass output for the English caption track;
- prepares a separate, more natural English source for downstream translation;
- translates into one or more target languages;
- supports local LLMs through LM Studio;
- can alternatively use OpenAI or Anthropic;
- supports terminology glossaries for consistent names and specialist language;
- writes intermediate passes and a pipeline log so you can inspect what happened; and
- provides `--dry-run` for inspecting the file and chunk layout without contacting any language model.

The current pipeline always performs the English review pass. For non-English targets, it also prepares a separate English translation source before translating. These are model-generated edits, not human review; inspect the output before publishing or delivering it.

Common inline HTML formatting is restored on a best-effort basis. Complex positioning, color, karaoke, or nonstandard markup and malformed cues may need manual repair.

### Supported target languages

| Code | Language |
| --- | --- |
| `en_US` | English review-pass output |
| `zh_CN` | Simplified Chinese |
| `hi_IN` | Hindi |
| `es_LA` | Latin American Spanish |
| `ar_AR` | Arabic |
| `fr_FR` | French |
| `de_DE` | German |
| `ja_JP` | Japanese |
| `ko_KR` | Korean |
| `pt_BR` | Brazilian Portuguese |
| `sv_SE` | Swedish |
| `nb_NO` | Norwegian |
| `nl_NL` | Dutch |
| `af_ZA` | Afrikaans |

You can pass a code or its language name, such as `fr_FR` or `French`.

## Requirements

You will need:

- Python 3.12 or newer;
- an SRT subtitle file; and
- one of the following:
  - a local language model served by LM Studio;
  - an OpenAI API key; or
  - an Anthropic API key.

For local translation, you do not need an OpenAI or Anthropic API key. Mae Captions uses a non-secret placeholder when talking to the default local LM Studio server.

## Install Mae Captions from source

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/chadmzoghby-alt/mae-captions.git
cd mae-captions
python -m venv .venv
```

On Windows PowerShell, activate it with:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux, activate it with the Python command available on your system (`python3` is common):

```bash
source .venv/bin/activate
```

Then install and check the CLI:

```bash
python -m pip install .
mae-captions --version
mae-captions --help
```

## Translate SRT subtitles with LM Studio

1. Install [LM Studio](https://lmstudio.ai/), download a model that can translate English into your target language, and load it.
2. Open LM Studio's **Developer** area and start the local server. Its OpenAI-compatible examples use port `1234`; Mae Captions expects the base URL to include `/v1`.
3. In PowerShell, confirm the server is responding and note the model identifier returned under `data`:

```powershell
Invoke-RestMethod http://localhost:1234/v1/models
```

4. Use that identifier in place of `YOUR_LOCAL_MODEL_ID`.

Windows PowerShell:

```powershell
mae-captions input.srt --targets de_DE --provider lmstudio --model YOUR_LOCAL_MODEL_ID --base-url http://localhost:1234/v1
```

If the input path contains spaces, quote it:

```powershell
mae-captions ".\My Subtitles\episode 1.srt" --targets de_DE --provider lmstudio --model YOUR_LOCAL_MODEL_ID --base-url http://localhost:1234/v1
```

macOS or Linux:

```bash
mae-captions input.srt \
  --targets de_DE \
  --provider lmstudio \
  --model YOUR_LOCAL_MODEL_ID \
  --base-url http://localhost:1234/v1
```

For example, replace `de_DE` with `French`, `ja_JP`, or another supported language. You can request several languages in one run:

```bash
mae-captions input.srt \
  --targets fr_FR de_DE es_LA \
  --provider lmstudio \
  --model YOUR_LOCAL_MODEL_ID \
  --base-url http://localhost:1234/v1
```

Before processing private or lengthy material, try the included synthetic fixture:

```powershell
mae-captions tests\fixtures\synthetic.srt --targets fr_FR --provider lmstudio --model YOUR_LOCAL_MODEL_ID --base-url http://localhost:1234/v1
```

If the model-list request or translation fails, confirm that the model is loaded, the LM Studio server is running, the port matches, and the model identifier is exact. Mae Captions does not currently select or load a model for you.

I do not prescribe a single beginner model yet. Start with an instruction-tuned model that LM Studio reports will fit in your available memory and that supports English and your target language. Hardware and memory requirements vary substantially by model and quantization.

## Preview an SRT without using a model

Use dry-run mode to check parsing, chunking, and target resolution without making an LLM or hosted-provider request:

```bash
mae-captions input.srt --preset top5 --dry-run
```

The built-in `top5` preset produces reviewed English plus Simplified Chinese, Hindi, Latin American Spanish, and Arabic targets.

## Use OpenAI or Anthropic instead

Keep credentials out of configuration files and command arguments. Expose the relevant key to the Mae Captions process through your operating system or secret manager:

- `OPENAI_API_KEY` for OpenAI;
- `ANTHROPIC_API_KEY` for Anthropic.

Then select the provider and model:

```bash
mae-captions input.srt \
  --targets de_DE fr_FR \
  --provider openai \
  --model YOUR_MODEL_NAME
```

Provider access, availability, credentials, and usage charges belong to you. Mae Captions is not affiliated with LM Studio, OpenAI, or Anthropic.

## Results and intermediate files

When no input path is supplied, Mae Captions looks for `.srt` files in `./inputs`. By default, it writes results under `./outputs`; use `--output-root` to choose another location.

For `movie.srt`, the result looks like:

```text
outputs/
  movie/
    movie.en_US.srt
    movie.de_DE.srt
    movie.fr_FR.srt
    passes/
      pass4_en_US.srt
      pass4_translation_source.srt
      pipeline.log
      ...
```

The top-level language files are the normal SRT deliverables. The `passes` directory contains intermediate JSON and SRT files for review and troubleshooting. `pipeline.log` records the run and any retry or provider error. These intermediate files and logs can contain caption text and model output, so protect them like the source subtitles.

Use `--skip-existing` to resume a multi-language job without repeating finished languages, or `--force` to replace existing results.

## Configuration and glossary

Copy `config.example.yaml` to `config.yaml` if you want persistent, non-secret preferences. Pass it explicitly with `--config config.yaml`. CLI flags override configuration values.

Do not put provider credentials in the YAML file. Mae Captions accepts hosted-provider credentials only through environment variables.

You can also provide a glossary CSV containing `term,translation` pairs:

```bash
mae-captions input.srt \
  --targets fr_FR \
  --provider lmstudio \
  --model YOUR_LOCAL_MODEL_ID \
  --base-url http://localhost:1234/v1 \
  --glossary glossary.csv
```

The glossary helps protect names and domain terminology during English review and encourages consistent translated terms.

## Privacy and safety

When `--provider lmstudio` points to `localhost` and your model runs locally, Mae Captions sends caption text only to that configured local model endpoint rather than to OpenAI or Anthropic. Mae Captions makes no additional application-level network request during that translation path. LM Studio and the selected model are separate software, so review their settings and behavior independently. When you select a hosted provider, that provider receives the caption text sent for review and translation.

The `--dry-run` path makes no model request. Routine tests use original synthetic text and block network access during the CLI smoke test.

Read [PRIVACY.md](PRIVACY.md) before processing sensitive material. Never commit real caption files, credentials, generated output folders, or logs to this repository.

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

I developed and locally validated the current alpha on Windows. The repository includes CI definitions for Linux, Windows, and macOS; cross-platform results will be recorded after the first public CI run.

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and [SUPPORT.md](SUPPORT.md) before opening an issue or report.

## Licensing

Mae Captions is source-available under the [PolyForm Noncommercial License 1.0.0](LICENSE), with a narrow [Independent Freelancer Exception](FREELANCER_EXCEPTION.md): one independent freelancer may personally use an unmodified official copy to produce static deliverables for clients.

Commercial or business use by companies, employers, agencies, partnerships, or teams requires a separate written commercial license, except for the single-person business vehicle allowed by the Freelancer Exception. Operating Mae Captions as a hosted service or providing hosted access to it, embedded uses, commercial redistribution, and commercial use of modified versions also require a commercial license. The base license continues to permit genuine noncommercial purposes and the qualifying organizations it lists. Read the [Licensing Guide](LICENSING.md) before relying on the freelancer permission.

The software is not offered under an OSI-approved open-source license. Direct dependencies remain governed by their own licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Project names and logos are governed separately by [TRADEMARKS.md](TRADEMARKS.md).
