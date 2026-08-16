# Workflow, Output, and Limitations

Mae Captions handles SRT structure while the selected language model handles English review and translation.

## What the pipeline does

Mae Captions:

- reads standard SubRip (`.srt`) files with encoding detection;
- keeps timecodes away from the LLM;
- preserves and restores common inline formatting such as italics and bold text;
- groups adjacent cues so the model can understand sentences across boundaries;
- creates a conservative AI review pass for the English caption track;
- prepares a clearer English source for non-English translation;
- translates into one or more target languages;
- rebuilds the SRT deterministically;
- writes intermediate passes and a pipeline log; and
- supports a terminology glossary.

The review pass and prepared source are model-generated edits, not human review. Inspect them and each translated deliverable before publication.

Common inline HTML formatting is restored on a best-effort basis. Complex positioning, colors, karaoke markup, malformed cues, and nonstandard formatting may require manual repair.

## Supported targets

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

Pass a code or its language name, such as `fr_FR` or `French`.

## Output files

When no input path is supplied, Mae Captions looks for `.srt` files under `./inputs`. By default it writes under `./outputs`; use `--output-root` to choose another location.

For `movie.srt`, output resembles:

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

The top-level language files are the normal SRT deliverables. The `passes` directory contains intermediate JSON and SRT files used for inspection and troubleshooting. `pipeline.log` records the run and any retry or provider error.

These files can contain complete source captions and model output. Protect them like the original media and captions.

## Glossary behavior

A CSV glossary containing `term,translation` pairs helps preserve canonical names during English review and encourages consistent translated terminology. It guides the model but cannot guarantee compliance, so verify important terms in the final file.

## Local and hosted data paths

With `--provider lmstudio` and a local `localhost` server, caption requests go to that configured local endpoint rather than OpenAI or Anthropic. Mae Captions has no telemetry or analytics client and makes no extra application-level network request during this translation path.

Local-only processing still depends on how LM Studio, the model, the operating system, and the network are configured. Do not expose the server beyond `localhost` unless you understand and intend the consequences.

With `--provider openai` or `--provider claude`, the selected provider receives caption text and prompt instructions. Its terms, retention controls, account settings, and charges apply.

The `--dry-run` path creates no model provider. Automated smoke tests additionally block socket access.

See [PRIVACY.md](../PRIVACY.md) for the full data-handling statement.

## Current alpha limitations

- English source captions only for reliable review and source preparation. `--source auto` affects the later translation prompt; it does not remove this limitation.
- SRT input and output only.
- Command line only; no graphical interface or installer.
- Model quality and supported languages depend on the selected model.
- No built-in model downloader or loader.
- No CLI flags for temperature, context length, or reasoning state.
- Per-response model output is capped at 4,096 tokens.
- Best-effort recovery for formatting and model marker mistakes still requires human inspection.
