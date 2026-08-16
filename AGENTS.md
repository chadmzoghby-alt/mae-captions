# Mae Captions Public Repository Working Rules

This repository is the fresh-history public candidate for Mae Captions.

## Safety

- Never import another repository's `.git` directory or use an indiscriminate whole-tree copy.
- Never commit real subtitle inputs, generated outputs, pass artifacts, logs, credentials, or local configuration.
- Use synthetic, original fixtures for tests and examples.
- Keep API keys in environment variables or OS keychain storage; never config files or CLI arguments.
- Do not run paid/live provider translations during routine development or CI.
- Pin and review release automation dependencies and use least-privilege workflow permissions.
- Do not advertise a platform, signature, updater, or privacy property that has not been verified.

## Quality gates

Before committing implementation work, run the focused tests for the changed layer. The first public upload is limited to the Python command-line interface. Desktop, sidecar, and packaging checks remain deferred until those components are separately approved for publication.

Public-facing documentation and the license require human review before the first public push.
