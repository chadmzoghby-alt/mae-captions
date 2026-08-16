# Choosing Models and Local Settings

Mae Captions does not bundle, download, or load an LLM. You choose the model, run it in LM Studio or select a hosted provider, and pass its exact model ID to the CLI.

There is no universally best subtitle model. Test representative dialogue, names, slang, sentence fragments, and difficult subject matter in the language pair you actually need.

The recommendations below have three different evidence levels:

- **Personally tested:** the named local Gemma GGUF and my LM Studio starting settings.
- **Provider documented, not live-tested here:** Claude Haiku and GPT-5.6 Luna.
- **General selection guidance:** larger-versus-specialist model tradeoffs, which you should verify on your own language pair.

The project does not make live paid-provider calls during release validation.

## My local starting point

I currently start with:

| Setting | Starting value | Why |
| --- | --- | --- |
| Model type | Instruction-tuned, multilingual GGUF | Follows the marker-preservation and output-only instructions |
| Thinking or reasoning | Off | Translation is a direct generation task; hidden or visible reasoning adds latency and can interfere with clean output |
| Temperature | `0.5` | A practical balance between stable wording and natural language |
| Context window | `16,000` tokens | Ample room for Mae Captions' prompt, preceding context, and current chunk size |
| Output limit | `4,096` tokens | This is currently set by Mae Captions for each model response |

In LM Studio, context length is a **load setting** and is different from the maximum number of tokens generated. Mae Captions sends chunks of about 900 characters by default and currently requests at most 4,096 output tokens, so setting a 16,000-token context window does not make each answer 16,000 tokens long.

Mae Captions does not currently send a temperature or reasoning parameter. Set temperature and thinking behavior in LM Studio's per-model defaults, preset, prompt template, or model configuration as supported by that runtime and model. The CLI's explicit 4,096-token output cap still applies.

LM Studio documents [per-model defaults](https://lmstudio.ai/docs/app/advanced/per-model), [saved inference presets](https://lmstudio.ai/docs/app/presets), and a first-party REST API where supported models can receive a reasoning setting such as `off`. Mae Captions currently uses LM Studio's OpenAI-compatible Chat Completions endpoint rather than that first-party chat endpoint.

### Temperature is a starting point, not a rule

For subtitle translation, I would test `0.2`, `0.5`, and the model author's recommendation against the same short evaluation set:

- use the lowest value that remains natural and does not repeat or drop text;
- prefer consistency over creative variation;
- reject settings that lose `<<number>>` markers or add commentary; and
- keep the chosen setting fixed across a real job.

I use `0.5`. The model card for my current local choice recommends `temperature=1.0`, `top_p=0.95`, and `top_k=64` across its general use cases. That upstream advice is broader than translation, so test both rather than silently assuming either is optimal.

## The local model I have used most successfully

My current personal recommendation is:

```text
gemma-4-26B-A4B-it-ultra-uncensored-heretic-Q4_K_M.gguf
```

The matching third-party [Hugging Face repository](https://huggingface.co/llmfan46/gemma-4-26B-A4B-it-ultra-uncensored-heretic-GGUF) publishes a `Q4_K_M` GGUF quantization and explains its thinking controls and sampling suggestions.

This is not bundled with Mae Captions, maintained by Mae Captions, or guaranteed to fit your machine. Review the model card, files, provenance, license, and security implications before downloading it. The repository and filename can also change independently of this project.

Do not assume the model will fit because its name includes `A4B`; the complete quantized file, runtime overhead, and key-value cache must fit across the memory available to LM Studio. A longer context window also uses more memory. I have not published a minimum RAM or VRAM figure because I have not reproduced this model across enough hardware. Check LM Studio's fit estimate before loading it, reduce context length if necessary, or start with a smaller instruction model and evaluate it on the same captions.

## Sensitive subject matter

Models with strong refusal behavior may refuse, soften, or sanitize lawful dialogue involving religion, politics, conflict, sexuality, or other sensitive subjects. For that material, I recommend comparing an uncensored instruction fine-tune against a standard model and choosing the one that preserves meaning most faithfully.

An uncensored model is not automatically more accurate, neutral, private, or safe. It may produce offensive or fabricated language without warning. Use it only for lawful material, keep the model server local when privacy matters, and have a fluent human review the result in context.

## Larger models and specialist smaller models

A larger capable model will often handle nuance, pronouns, idioms, register, and long-range consistency better, provided it runs without excessive memory pressure or aggressive quantization. Model size alone does not prove translation quality.

A smaller model can be the better choice when it has been refined for the exact language pair or domain. For example, a specialist English-to-Chinese model may outperform a larger general chat model on that pair while using less memory and translating faster.

Choose by evaluation, not parameter count:

1. create a short, representative SRT containing easy and difficult lines;
2. translate it with the same Mae Captions settings;
3. compare meaning, naturalness, names, omissions, marker preservation, and refusals;
4. measure speed and memory use; and
5. only then start a full-length job.

## Thinking and reasoning

Turn thinking off for local subtitle translation when the model and runtime allow it. Mae Captions expects only corrected or translated text with structural markers; an exposed reasoning trace can break that contract, while hidden reasoning can add latency without a demonstrated benefit for routine chunks.

The tested Gemma model card says thinking is enabled by a prompt-template control token and disabled when that token is absent. LM Studio's own API supports a model-dependent `reasoning: "off"` setting. The exact switch varies by model and runtime, so confirm it with a single short translation and inspect the returned text before a long run.

## Hosted models

Hosted models send caption text outside your computer and may incur usage charges. Current availability, behavior, and pricing can change, so confirm the provider's documentation before starting a large file.

### Anthropic

**Evidence: provider documented; not live-tested with Mae Captions.**

For the Anthropic provider, I recommend starting by evaluating Claude Haiku for speed and cost, then testing a stronger model only if the translation quality is not sufficient:

```bash
mae-captions input.srt --targets fr_FR --provider claude --model claude-haiku-4-5
```

Anthropic's current [model-selection guide](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model) recommends Claude Haiku 4.5 as an efficiency-first starting point for high-volume, straightforward work. The [models overview](https://platform.claude.com/docs/en/about-claude/models/overview) lists `claude-haiku-4-5` as its API alias. Mae Captions does not enable Anthropic extended thinking.

### OpenAI

**Evidence: provider documented; not live-tested with Mae Captions.**

OpenAI's current [API model catalog](https://developers.openai.com/api/docs/models) positions GPT-5.6 Luna for cost-sensitive, high-volume workloads and lists Chat Completions support. However, it is a reasoning model, Mae Captions does not send OpenAI `reasoning_effort`, and this project has not made a live compatibility call. I therefore do not present Luna as a tested Mae Captions preset yet. If you evaluate `gpt-5.6-luna` through `--provider openai`, start with the synthetic fixture and inspect every pass before using real captions.

### Codex is separate

When I use Codex to work on Mae Captions itself, I choose `gpt-5.6-luna` for lightweight or high-volume work. OpenAI's current [Codex model guidance](https://learn.chatgpt.com/docs/models#deprecated-codex-models) identifies GPT-5.6 Luna as the successor to its earlier mini tier.

Codex is a development tool, not a Mae Captions provider. Selecting Luna in Codex does not configure a translation run.

## What to record for a reproducible job

Keep a private run note with:

- exact model repository and filename or hosted model ID;
- quantization;
- LM Studio and runtime version;
- temperature, context length, and thinking state;
- target language and glossary version;
- Mae Captions version; and
- a small reviewed evaluation result.

Do not put API keys, private captions, or provider responses in that note if it may be committed or shared.
