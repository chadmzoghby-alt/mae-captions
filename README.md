# Mae Captions — Local LLM SRT Subtitle Translation

**Translate SRT subtitles with an LLM running on your own computer.**

Mae Captions is a local-first Python command-line tool for reviewing and translating SubRip (`.srt`) caption files with large language models. I built it on Windows around [LM Studio](https://lmstudio.ai/), so you can run a local model and keep the translation path on hardware you control.

You can also use OpenAI or Anthropic when a hosted model suits the job better.

> [!IMPORTANT]
> Mae Captions `0.1.0` is an alpha CLI. There is no graphical interface, desktop installer, signed executable, or automatic updater yet.

> [!NOTE]
> Mae Captions is source-available, not open source. Noncommercial use and a narrow solo-freelancer exception are available; most other commercial use requires a separate license. See [Licensing](#licensing).

## Why Mae Captions?

Subtitle translation is more than translating a block of text. Dialogue crosses cue boundaries, terminology must remain consistent, and the timestamps must survive intact.

Mae Captions separates those jobs:

```text
English .srt -> Mae Captions -> local LLM -> translated .srt
                  |
                  +-> keeps timecodes and structure away from the model
```

The model handles language and context. Mae Captions parses, groups, and deterministically rebuilds the SRT structure.

## What it gives you

- **Local-first translation:** use an OpenAI-compatible model server at `localhost`.
- **No Mae Captions telemetry:** there is no analytics client or Mae-operated service.
- **Structure-aware output:** timecodes are not sent to the model or rebuilt by it.
- **Inspectable work:** intermediate passes and a pipeline log show what happened.
- **Model choice:** use a local instruction model, OpenAI, or Anthropic.
- **Terminology control:** supply a glossary for names and specialist terms.
- **Offline preview:** `--dry-run` parses and chunks an SRT without contacting a model.

The current alpha expects **English source captions**. It reviews the English track, prepares a translation source, and then creates one or more target-language SRT files. Always review model-generated captions before publishing or delivering them.

Mae Captions translates existing captions; it does not transcribe audio or create cue timings. I recommend creating and timing the source SRT in a dedicated tool such as [Subtitle Edit](https://github.com/SubtitleEdit/subtitleedit) before translating it.

## Quick start with LM Studio

You need Git, Python 3.12 or newer, an English `.srt` file, [LM Studio](https://lmstudio.ai/), and a local model that can translate into your target language.

```bash
git clone https://github.com/chadmzoghby-alt/mae-captions.git
cd mae-captions
python -m venv .venv
```

Activate the environment on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Or on macOS and Linux:

```bash
source .venv/bin/activate
```

Install Mae Captions:

```bash
python -m pip install .
mae-captions --version
```

Load a model in LM Studio, start its local server, and get the exact model identifier:

```powershell
(Invoke-RestMethod http://localhost:1234/v1/models).data.id
```

Then translate an SRT:

```powershell
mae-captions input.srt --targets de_DE --provider lmstudio --model YOUR_LOCAL_MODEL_ID --base-url http://localhost:1234/v1
```

By default, the translated file appears under `outputs/<input-name>/`. See [Workflow, Output, and Limitations](docs/workflow-and-output.md) for the exact layout.

Try the included synthetic fixture before using private or lengthy material:

```powershell
mae-captions tests\fixtures\synthetic.srt --targets fr_FR --provider lmstudio --model YOUR_LOCAL_MODEL_ID --base-url http://localhost:1234/v1
```

Or inspect a file without making any model request:

```bash
mae-captions input.srt --preset top5 --dry-run
```

See the [Getting Started Guide](docs/getting-started.md) for detailed setup, macOS/Linux commands, multiple languages, hosted providers, configuration, and troubleshooting.

## Choosing a model

Model choice matters. Larger capable models often handle nuance better, while a smaller model refined for one language pair can be faster and sometimes better for that pair.

Read [Choosing Models and Local Settings](docs/models-and-settings.md) for my personally tested Gemma GGUF, settings for thinking, temperature and context, guidance for sensitive subject matter, specialist translation models, Claude Haiku, and GPT-5.6 Luna.

## Documentation

| Guide | Use it for |
| --- | --- |
| [Getting Started](docs/getting-started.md) | Installation, LM Studio, commands, hosted providers, and troubleshooting |
| [Models and Settings](docs/models-and-settings.md) | Local-model selection, tested settings, sensitive content, Claude, and OpenAI |
| [Workflow and Output](docs/workflow-and-output.md) | Pipeline behavior, languages, files, glossaries, privacy, and limitations |
| [Development](docs/development.md) | Local tests, repository checks, and alpha contribution policy |
| [Privacy](PRIVACY.md) | What stays local, what leaves the computer, and what is written to disk |
| [Licensing Guide](LICENSING.md) | Noncommercial use, the freelancer exception, and commercial licensing |

## Privacy

With `--provider lmstudio` and a local `localhost` endpoint, Mae Captions sends captions to that configured local server rather than OpenAI or Anthropic. Mae Captions makes no extra application-level network request on this path. LM Studio, downloaded models, operating-system services, and network configuration are separate, so review them independently.

Selecting a hosted provider sends caption text and instructions to that provider. Intermediate files and logs can also contain the full caption text. Read the [Privacy Guide](PRIVACY.md) before processing sensitive material.

## Licensing

Mae Captions uses the [PolyForm Noncommercial License 1.0.0](LICENSE) plus a narrow [Independent Freelancer Exception](FREELANCER_EXCEPTION.md). A qualifying independent freelancer may use an unmodified official copy to produce static client deliverables.

Companies, employers, agencies, partnerships, and teams generally need a separate written commercial license. Hosted access, embedded use, commercial redistribution, and commercial use of modified versions also require a commercial license. Read the [Licensing Guide](LICENSING.md) before relying on the exception.

The license is not OSI-approved. Dependencies retain their own licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Names and logos are covered separately by [TRADEMARKS.md](TRADEMARKS.md).
