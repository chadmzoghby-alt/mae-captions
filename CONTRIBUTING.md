# Participating in Mae Captions

Mae Captions welcomes focused bug reports and feature requests for the public CLI. The initial alpha does not accept external code, documentation, design, or test contributions.

## Before opening an issue

- Search existing issues first.
- Keep real caption content, credentials, provider responses, logs, and generated outputs out of issues and commits.
- Use only original synthetic fixtures.
- Do not make live provider calls as part of tests.
- Describe one reproducible problem or focused proposal per issue.

## External pull requests

Do not submit external pull requests or other patches during the initial alpha. Unsolicited contributions will not be reviewed or merged, and submission does not grant or imply acceptance of any rights.

The project may open contributions later after publishing contributor terms that identify the legal recipient of the necessary copyright and patent permissions. Until then, use an issue to describe a bug or proposed change without attaching third-party code or substantial implementation text.

## Maintainer checks

Maintainers create an isolated Python 3.12 environment, install `requirements.txt` and `requirements-ci.txt`, and run the commands in the README's development section. Changes must pass the repository-safety, quality, cross-platform unit-test, package, and dependency-review jobs. Third-party code or text must be identified before inclusion and compatible with the source-available and commercial distribution model.

## Community conduct decision

The initial CLI release does not include a standalone community code-of-conduct document. Respectful, constructive, and privacy-conscious participation is required. Harassment, disclosure of another person's private data, and hostile conduct are not accepted. This decision can be revisited as the contributor community grows.
