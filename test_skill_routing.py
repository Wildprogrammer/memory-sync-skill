#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Agent Skill routing index generation."""

from __future__ import annotations

import importlib.util
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


class SkillRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_main()

    def test_new_skill_gets_pending_route_and_markdown_sections(self) -> None:
        records = [
            {
                "name": "openai-codex-operator",
                "description": "Run OpenAI Codex CLI from OpenClaw for coding tasks.",
                "agent": "openclaw",
                "level": "workspace",
                "relative_path": "openai-codex-operator/SKILL.md",
                "path": "C:/skills/openai-codex-operator/SKILL.md",
                "sha256": "oldsha",
                "last_modified": "2026-06-07T16:59:52",
                "frontmatter_valid": True,
                "enabled": True,
            },
            {
                "name": "Claude Code CLI for OpenClaw",
                "description": "Install, authenticate, and use Claude Code CLI as a native coding tool for any OpenClaw agent system.",
                "agent": "openclaw",
                "level": "workspace",
                "relative_path": "claude-code-cli-openclaw/SKILL.md",
                "path": "C:/skills/claude-code-cli-openclaw/SKILL.md",
                "sha256": "newsha",
                "last_modified": "2026-06-07T23:20:10",
                "frontmatter_valid": True,
                "enabled": True,
            },
        ]
        previous = [
            {
                **records[0],
                "identity": "openclaw|workspace|openai-codex-operator/SKILL.md",
                "primary_category": "Agent 与自动化编排",
                "related_categories": ["开发与调试"],
                "use_when": ["Codex delegation"],
                "avoid_when": ["Not for Claude Code"],
                "routing_status": "confirmed",
                "routing_confidence": 0.95,
                "routing_source": "agent",
                "routing_reviewed_sha256": "oldsha",
            }
        ]

        routed = self.mod.route_skill_records("openclaw", records, previous)
        new_skill = next(item for item in routed if item["name"] == "Claude Code CLI for OpenClaw")

        self.assertEqual(new_skill["primary_category"], "Agent 与自动化编排")
        self.assertIn("开发与调试", new_skill["related_categories"])
        self.assertEqual(new_skill["routing_status"], "pending_review")
        self.assertEqual(new_skill["identity"], "openclaw|workspace|claude-code-cli-openclaw/SKILL.md")

        app = object.__new__(self.mod.MemorySync)
        app.preferred_language = lambda: "zh"
        markdown = app.agent_skill_markdown("openclaw", routed, "2026-06-07T23:43:51")

        for heading in ["## 快速路由", "## 分类匹配指南", "## 冲突处理规则", "## 完整 Skill 清单", "## 质量问题"]:
            self.assertIn(heading, markdown)
        self.assertIn("Claude Code CLI for OpenClaw", markdown)
        self.assertIn("新增待复核", markdown)

    def test_confirmed_route_is_preserved_when_sha_unchanged(self) -> None:
        record = {
            "name": "memory-sync",
            "description": "Synchronize agent memory and portable context.",
            "agent": "openclaw",
            "level": "workspace",
            "relative_path": "memory-sync/SKILL.md",
            "path": "C:/skills/memory-sync/SKILL.md",
            "sha256": "same",
            "last_modified": "2026-06-07T12:00:00",
            "frontmatter_valid": True,
            "enabled": True,
        }
        previous = [
            {
                **record,
                "identity": "openclaw|workspace|memory-sync/SKILL.md",
                "primary_category": "记忆与上下文",
                "related_categories": ["文档与知识管理"],
                "use_when": ["Preserve agent memory"],
                "avoid_when": ["Temporary context only"],
                "routing_status": "confirmed",
                "routing_confidence": 0.99,
                "routing_source": "agent",
                "routing_reviewed_sha256": "same",
            }
        ]

        routed = self.mod.route_skill_records("openclaw", [record], previous)
        self.assertEqual(routed[0]["routing_status"], "confirmed")
        self.assertEqual(routed[0]["routing_source"], "agent")
        self.assertEqual(routed[0]["use_when"], ["Preserve agent memory"])
        self.assertEqual(routed[0]["avoid_when"], ["Temporary context only"])


if __name__ == "__main__":
    unittest.main()
