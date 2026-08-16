# Security Policy

## Supported version

Security fixes currently target the latest `0.1.x` CLI source release.

## Report a vulnerability

Do not disclose a suspected vulnerability in a public issue. Use GitHub's private vulnerability reporting option when it is available for this repository. If that option is unavailable, contact the maintainer through the GitHub profile linked to the repository and request a private reporting channel.

Include the affected version, operating system, reproduction steps, likely impact, and whether credentials or private caption data may have been exposed. Do not include working credentials, real caption content, or other people's private data.

## Credential handling

Mae Captions accepts hosted-provider credentials from process environment variables only. It does not accept credentials in its YAML configuration or command-line arguments. Logs and bug reports should still be reviewed before sharing because provider SDK errors may contain request context.

