#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for memory candidate filtering quality gates."""

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


class CandidateFilteringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_main()

    def test_routine_heartbeat_status_is_noise(self) -> None:
        text = "心跳自检：Gateway healthy，Redis 运行正常，安全检查通过，无错误。"

        self.assertEqual(self.mod.noise_reason_for_text(text), "routine_status")

    def test_failure_recovery_status_enters_review(self) -> None:
        text = (
            "心跳自检发现 rate_limit 请求失败，原因是并发过高；已改成退避重试并验证恢复。"
            "后续遇到 429 时先降低并发。"
        )

        self.assertIsNone(self.mod.noise_reason_for_text(text))

    def test_memory_sync_self_log_is_noise(self) -> None:
        text = (
            "memory-sync status: Candidates: 166, Coverage: daily_files=19, "
            "skipped=81, review apply success, S1=10, S2=10."
        )

        self.assertEqual(self.mod.noise_reason_for_text(text), "memory_sync_self_log")

    def test_memory_sync_failure_lesson_enters_review(self) -> None:
        text = (
            "memory-sync review apply failed because decisions JSON used unsupported paths. "
            "Fix: preserve source_file/source_anchor through review apply and add validation."
        )

        self.assertIsNone(self.mod.noise_reason_for_text(text))

    def test_memory_sync_summary_with_unrelated_fix_is_noise(self) -> None:
        text = (
            "记忆库每日同步 cron (05:00): Candidates: 28; Coverage: daily_files=14. "
            "审核候选时保留 1 条 Hermes base URL 修复经验，其余为状态快照。"
        )

        self.assertEqual(self.mod.noise_reason_for_text(text), "memory_sync_self_log")

    def test_memory_sync_apply_success_summary_is_noise(self) -> None:
        text = (
            "记忆库每日同步 cron (05:00): `review apply` 成功：added=1, merged=0, "
            "discarded=27；`status` 正常：Memories=197（S1=73, S2=64）。"
        )

        self.assertEqual(self.mod.noise_reason_for_text(text), "memory_sync_self_log")

    def test_temporary_test_path_is_noise(self) -> None:
        text = (
            "测试文件位置：C:/tmp/obsidian/"
            "memory-sync-test-vault-5/latest-pack.json，只用于本次临时验证。"
        )

        self.assertEqual(self.mod.noise_reason_for_text(text), "temporary_test_path")


if __name__ == "__main__":
    unittest.main()
