# Open Source Audit

Prepared for public release of Memory Sync v2.

## Release Scope

Memory Sync v2 is a local-first OpenClaw companion and multi-agent context portability skill. It syncs OpenClaw memory into Obsidian, ingests explicit handoff summaries or project captures from supported agents, stores original records under `_agents/<agent>/daily/`, and exports portable context under `_shared/context/`.

## Included

- `SKILL.md`
- `README.md`
- `LICENSE`
- `SECURITY.md`
- `.env.example`
- `.gitignore`
- `agents/openai.yaml`
- `config/*.json`
- `scripts/main.py`
- `scripts/__init__.py`
- `test_config.py`

## Excluded

- `.env`
- `__pycache__/`
- generated Obsidian vault files
- generated memory indexes from private data
- Git remotes and local Git metadata

## Sanitization Checks

- Default paths use `~` and generic vault names.
- User-specific allowlist examples were removed from `config/keywords.json`.
- README examples use generic memory-sync terms.
- README includes English and Chinese introductions.
- Public examples use placeholder paths such as `/path/to/memory-sync-skill`.
- No API keys or tokens are included.

## Validation

Run before publishing:

```bash
python -B -m py_compile scripts/main.py
python scripts/main.py help
python scripts/main.py diagnose "remember memory-sync trigger cooldown Obsidian index"
```
