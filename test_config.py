#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate memory-sync local configuration."""

from pathlib import Path
import os


ROOT = Path(__file__).resolve().parent


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def expand_path(value: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(value)))


def main() -> int:
    load_env(ROOT / ".env")

    openclaw = expand_path(os.environ.get("OPENCLAW_WORKSPACE", "~/.openclaw/workspace"))
    vault = expand_path(os.environ.get("OBSIDIAN_VAULT_PATH", "~/Documents/obsidian/vault"))

    print("=" * 60)
    print("Memory-Sync configuration check")
    print("=" * 60)

    print(f"\nOpenClaw workspace: {openclaw}")
    print("  OK path exists" if openclaw.exists() else "  WARN path does not exist")
    print("  OK MEMORY.md exists" if (openclaw / "MEMORY.md").exists() else "  WARN MEMORY.md not found")
    print("  OK memory dir exists" if (openclaw / "memory").exists() else "  WARN memory dir not found")

    print(f"\nObsidian vault: {vault}")
    print("  OK path exists" if vault.exists() else "  WARN path does not exist")
    print("  OK git repo" if (vault / ".git").exists() else "  WARN not a git repo; git sync needs a configured repository")

    print("\nGit sync:")
    print(f"  GIT_SYNC_ENABLED={os.environ.get('GIT_SYNC_ENABLED', 'false')}")
    print(f"  GIT_REMOTE={os.environ.get('GIT_REMOTE', 'origin')}")
    print(f"  GIT_BRANCH={os.environ.get('GIT_BRANCH', 'main')}")

    print("\n" + "=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
