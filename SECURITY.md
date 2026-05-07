# Security Policy

## Supported Use

This project is a local memory synchronization skill. It is designed to read local OpenClaw memory files, write derived files into a local Obsidian vault, and optionally commit those derived files with Git.

## Sensitive Data

Do not commit:

- `.env`
- API keys or access tokens
- real Obsidian vault contents
- generated memory indexes containing private memories
- personal workspace paths

Only `.env.example` and empty/configurable rule files should be committed.

## Reporting

For security issues, open a private advisory or contact the project maintainer through the repository's preferred private channel.
