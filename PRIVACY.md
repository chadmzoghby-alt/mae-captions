# Privacy and Provider Data

Mae Captions does not include telemetry, analytics, or a Mae-operated network service.

## What leaves the computer

When Anthropic or OpenAI is selected, Mae Captions sends caption text and prompt instructions to that provider. The provider's terms, retention rules, privacy policy, account settings, and charges apply. Users supply their own credentials and pay their own provider costs.

When LM Studio is selected with a local server URL, requests are sent to that configured server. Processing remains local only when the server, model, and URL are local and the surrounding system does not proxy or forward requests.

The `--dry-run` path parses and chunks files without creating a provider client. The CI smoke test additionally blocks socket access.

## Data stored locally

By default, Mae Captions reads explicit input paths or `.srt` files under `./inputs`. It writes intermediate passes, final SRT files, JSON metadata, and `pipeline.log` beneath `./outputs`. A different output root can be selected through configuration or `--output-root`.

These files can contain the full caption text. Protect, retain, and delete them according to your own data-handling requirements. Do not attach them to public issues unless the content is original, synthetic, and safe to share.

## Credentials

Hosted-provider credentials are read from `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in the Mae Captions process environment. They are not written to Mae Captions configuration by the CLI. Users are responsible for choosing a secure operating-system or secret-manager mechanism for exposing those variables.

Mae Captions is not affiliated with Anthropic, OpenAI, or LM Studio.

