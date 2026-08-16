# Getting Started with Mae Captions

This guide takes you from an English SRT file to translated SRT output. The primary setup uses a local LLM through LM Studio, so no OpenAI or Anthropic API key is required.

## Before you start

You need:

- Python 3.12 or newer;
- Git, if you are cloning the repository;
- an English-language SubRip (`.srt`) file; and
- either LM Studio with a local model, an OpenAI API key, or an Anthropic API key.

Mae Captions translates existing SRT files. It does not transcribe audio or create cue timings. I recommend creating and checking the source captions in a dedicated authoring tool such as [Subtitle Edit](https://github.com/SubtitleEdit/subtitleedit) first.

The alpha review and translation-source prompts assume English. Do not rely on `--source auto` to make non-English source captions safe to process in this release.

## Install from source

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/chadmzoghby-alt/mae-captions.git
cd mae-captions
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you do not need to change the machine's execution policy. Run the environment's executables directly:

```powershell
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\mae-captions.exe --version
```

Or on macOS and Linux (`python3` may be the available command):

```bash
source .venv/bin/activate
```

Install and check the CLI:

```bash
python -m pip install .
mae-captions --version
mae-captions --help
```

## Start the local model server

1. Install [LM Studio](https://lmstudio.ai/).
2. Download and load an instruction-tuned model that supports English and your target language.
3. Open LM Studio's **Developer** area and start the local server on port `1234`.
4. Keep it bound to `localhost` unless you intentionally want other devices to reach it.

Mae Captions expects an OpenAI-compatible base URL ending in `/v1`:

```text
Mae Captions -> http://localhost:1234/v1 -> local model
```

Confirm that the server is responding and copy the exact model ID returned under `data`.

Windows PowerShell:

```powershell
(Invoke-RestMethod http://localhost:1234/v1/models).data.id
```

macOS or Linux:

```bash
curl http://localhost:1234/v1/models
```

See [Choosing Models and Local Settings](models-and-settings.md) before committing to a large download.

## Translate one language

Replace `YOUR_LOCAL_MODEL_ID` with the identifier returned by the server.

Windows PowerShell:

```powershell
mae-captions input.srt --targets de_DE --provider lmstudio --model YOUR_LOCAL_MODEL_ID --base-url http://localhost:1234/v1
```

The CLI prints each pipeline phase and chunk as it runs. Local speed varies widely by model and hardware. The completed SRT appears under `outputs/<input-name>/` by default; see [Workflow, Output, and Limitations](workflow-and-output.md).

Quote paths that contain spaces:

```powershell
mae-captions ".\My Captions\episode 1.srt" --targets de_DE --provider lmstudio --model YOUR_LOCAL_MODEL_ID --base-url http://localhost:1234/v1
```

macOS or Linux:

```bash
mae-captions input.srt \
  --targets de_DE \
  --provider lmstudio \
  --model YOUR_LOCAL_MODEL_ID \
  --base-url http://localhost:1234/v1
```

You can pass a language code or name, such as `fr_FR` or `French`.

## Translate several languages

Windows PowerShell:

```powershell
mae-captions input.srt --targets fr_FR de_DE es_LA --provider lmstudio --model YOUR_LOCAL_MODEL_ID --base-url http://localhost:1234/v1
```

macOS or Linux:

```bash
mae-captions input.srt \
  --targets fr_FR de_DE es_LA \
  --provider lmstudio \
  --model YOUR_LOCAL_MODEL_ID \
  --base-url http://localhost:1234/v1
```

Use `--skip-existing` to resume without repeating finished languages, or `--force` to replace existing results.

## Test before using real captions

The repository includes a small synthetic fixture:

```powershell
mae-captions tests\fixtures\synthetic.srt --targets fr_FR --provider lmstudio --model YOUR_LOCAL_MODEL_ID --base-url http://localhost:1234/v1
```

Dry-run mode parses the SRT, resolves targets, and shows chunking without creating a provider client:

```bash
mae-captions input.srt --preset top5 --dry-run
```

The `top5` preset requests reviewed English, Simplified Chinese, Hindi, Latin American Spanish, and Arabic.

## Use OpenAI or Anthropic

Keep credentials out of YAML files and command arguments. Expose the appropriate key through your operating system or secret manager:

- `OPENAI_API_KEY` for OpenAI;
- `ANTHROPIC_API_KEY` for Anthropic.

Then select the provider and an API model ID:

```bash
mae-captions input.srt \
  --targets de_DE fr_FR \
  --provider openai \
  --model YOUR_OPENAI_MODEL_ID
```

For Anthropic:

```bash
mae-captions input.srt \
  --targets de_DE fr_FR \
  --provider claude \
  --model claude-haiku-4-5
```

Provider access, retention, account settings, availability, and charges belong to you. Check current model IDs before starting a long run.

## Persistent configuration and glossaries

Copy `config.example.yaml` to `config.yaml` for non-secret preferences, then pass it explicitly:

```bash
mae-captions input.srt --config config.yaml
```

CLI flags override YAML values. Do not put API keys in the configuration file.

A glossary CSV contains `term,translation` pairs and helps preserve names and specialist terminology:

Windows PowerShell:

```powershell
mae-captions input.srt --targets fr_FR --provider lmstudio --model YOUR_LOCAL_MODEL_ID --base-url http://localhost:1234/v1 --glossary glossary.csv
```

macOS or Linux:

```bash
mae-captions input.srt \
  --targets fr_FR \
  --provider lmstudio \
  --model YOUR_LOCAL_MODEL_ID \
  --base-url http://localhost:1234/v1 \
  --glossary glossary.csv
```

## Troubleshooting

If the model-list request or translation fails:

1. confirm that LM Studio is running and the model is loaded;
2. confirm the server port and `/v1` base URL;
3. copy the exact model identifier from `/v1/models`;
4. confirm the model fits in available memory at the selected context length;
5. try the synthetic fixture; and
6. inspect the run's `passes/pipeline.log` without sharing private caption text publicly.

If `python` opens the Microsoft Store or reports the wrong version, install Python 3.12 or newer and use its `py` launcher or full executable path. If `mae-captions` is not found, activate the virtual environment or run `.\.venv\Scripts\mae-captions.exe` directly on Windows.

See [Workflow, Output, and Limitations](workflow-and-output.md) for output paths and the supported language list.
