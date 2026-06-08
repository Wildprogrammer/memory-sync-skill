#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for local agent conversation scanners."""

from __future__ import annotations

import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MAIN_PATH = ROOT / "scripts" / "main.py"


def load_main():
    spec = importlib.util.spec_from_file_location("memory_sync_main", MAIN_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConversationScannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_main()

    def bare_app(self):
        app = object.__new__(self.mod.MemorySync)
        app.logs = []
        app.log = lambda message: app.logs.append(message)
        return app

    def test_codex_rollout_files_include_archived_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sessions = root / "sessions" / "2026" / "06" / "08"
            archived = root / "archived_sessions"
            sessions.mkdir(parents=True)
            archived.mkdir(parents=True)
            live = sessions / "rollout-live.jsonl"
            old = archived / "rollout-old.jsonl"
            live.write_text("{}", encoding="utf-8")
            old.write_text("{}", encoding="utf-8")

            app = self.bare_app()
            app.codex_home = lambda: root

            files = [path.name for path in app.codex_rollout_files()]

        self.assertEqual(set(files), {"rollout-live.jsonl", "rollout-old.jsonl"})

    def test_parse_opencode_export_json_to_conversation(self) -> None:
        app = self.bare_app()
        payload = {
            "info": {
                "id": "ses_test",
                "title": "Investigate parser",
                "directory": "D:/repo",
                "time": {"created": 1774448438489, "updated": 1774448440000},
            },
            "messages": [
                {
                    "info": {
                        "id": "msg_user",
                        "role": "user",
                        "time": {"created": 1774448439000},
                    },
                    "parts": [{"type": "text", "text": "Fix the flaky test"}],
                },
                {
                    "info": {
                        "id": "msg_assistant",
                        "role": "assistant",
                        "time": {"created": 1774448440000},
                    },
                    "parts": [{"type": "text", "text": "The assertion should wait for the UI."}],
                },
            ],
        }

        conversations = app.parse_opencode_export(payload, Path("opencode-export.json"), "2026-03-25", False)

        self.assertEqual(list(conversations.keys()), [("2026-03-25", "ses_test")])
        events = conversations[("2026-03-25", "ses_test")]["events"]
        self.assertEqual([event["role"] for event in events], ["user", "assistant"])
        self.assertEqual(events[0]["text"], "Fix the flaky test")
        self.assertIn("OpenCode export", conversations[("2026-03-25", "ses_test")]["meta"]["originator"])

    def test_read_opencode_sqlite_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "opencode.db"
            con = sqlite3.connect(db)
            try:
                con.execute(
                    "create table session (id text, project_id text, parent_id text, slug text, directory text, "
                    "title text, version text, share_url text, summary_additions integer, summary_deletions integer, "
                    "summary_files integer, summary_diffs text, revert text, permission text, time_created integer, "
                    "time_updated integer, time_compacting integer, time_archived integer, workspace_id text, path text, "
                    "agent text, model text, cost real, tokens_input integer, tokens_output integer, "
                    "tokens_reasoning integer, tokens_cache_read integer, tokens_cache_write integer, metadata text)"
                )
                con.execute(
                    "create table message (id text, session_id text, time_created integer, time_updated integer, data text)"
                )
                con.execute(
                    "create table part (id text, message_id text, session_id text, time_created integer, time_updated integer, data text)"
                )
                con.execute(
                    "insert into session (id, directory, title, version, time_created, time_updated) values (?, ?, ?, ?, ?, ?)",
                    ("ses_sql", "D:/repo", "SQLite session", "1.2.27", 1774448438000, 1774448442000),
                )
                con.execute(
                    "insert into message values (?, ?, ?, ?, ?)",
                    (
                        "msg_user",
                        "ses_sql",
                        1774448439000,
                        1774448439000,
                        json.dumps({"role": "user", "agent": "build"}),
                    ),
                )
                con.execute(
                    "insert into part values (?, ?, ?, ?, ?, ?)",
                    (
                        "part_user",
                        "msg_user",
                        "ses_sql",
                        1774448439000,
                        1774448439000,
                        json.dumps({"type": "text", "text": "Remember this OpenCode lesson"}),
                    ),
                )
                con.commit()
            finally:
                con.close()

            app = self.bare_app()
            conversations = app.read_opencode_sqlite(db, "2026-03-25", False)

        self.assertEqual(list(conversations.keys()), [("2026-03-25", "ses_sql")])
        event = conversations[("2026-03-25", "ses_sql")]["events"][0]
        self.assertEqual(event["role"], "user")
        self.assertEqual(event["text"], "Remember this OpenCode lesson")


if __name__ == "__main__":
    unittest.main()
