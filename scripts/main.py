#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OpenClaw memory sync with a single canonical index."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


ROOT = Path(__file__).resolve().parents[1]
INDEX_META = "_meta"
INDEX_NAME = "openclaw_memory_index.json"
PROFILE_NAME = "user_profile.json"
OBSIDIAN_INDEX_FILE = "03-Reference/OpenClaw\u8bb0\u5fc6\u7d22\u5f15.md"
PROFILE_MD_FILE = "03-Reference/User\u753b\u50cf.md"
MEMORY_DASHBOARD_FILE = "03-Reference/Memory Dashboard.md"
MEMORY_PAGES_DIR = "03-Reference/Memories"
CONTEXT_DIR = "_context"
CONTEXT_JSON = f"{CONTEXT_DIR}/agent_context.json"
ADAPTER_NAMES = ("codex", "claude", "openclaw", "opencode", "hermes-agent")
AGENTS_DIR = "_agents"
SHARED_DIR = "_shared"
SHARED_CONTEXT_DIR = f"{SHARED_DIR}/context"
SHARED_MEMORY_INDEX = f"{SHARED_DIR}/shared_memory_index.json"
SHARED_PROFILE_JSON = f"{SHARED_DIR}/user_profile.json"
SHARED_CONTEXT_JSON = f"{SHARED_DIR}/agent_context.json"
PERMANENT_DIR = "03-Reference/OpenClaw-Permanent"
DAILY_DIR = "memory"
VAULT_DAILY_DIR = "02-Lessons/OpenClaw-Daily"
STAGES = ("S1", "S2", "S3", "S4")
PREVIOUS_STAGE = {"S2": "S1", "S3": "S2"}
RESERVED_INDEX_KEYS = {INDEX_META, "memories", "daily_refs", "processed_dates", "version", "updated_at"}
ALLOWED_SOURCE_PREFIXES = (f"{VAULT_DAILY_DIR}/", f"{PERMANENT_DIR}/")
LEGACY_SOURCE_MARKERS = ("memory/.dreams/session-corpus/", "main/sessions/", ".jsonl")
MIN_COMPACT_LENGTH = 80
STRONG_KEYWORD_ALLOWLIST: set[str] = set()
OPENCLAW_RECALL_MIN_SCORE = 0.70
OPENCLAW_RECALL_MIN_RECALLS = 1
OPENCLAW_RECALL_MAX_CANDIDATES = 80
OPENCLAW_DREAM_MIN_CONFIDENCE = 0.58

TRIGGER_WORDS = [
    "记得",
    "记忆",
    "回忆",
    "上次",
    "之前",
    "以前",
    "曾经",
    "历史",
    "背景",
    "上下文",
    "仔细想想",
    "想起来",
    "记录",
    "复盘",
    "经验",
    "remember",
    "memory",
    "recall",
    "previous",
    "last time",
    "context",
    "覚えて",
]

BLACKLIST_PATTERNS = [
    r"\bheartbeat\b",
    r"\bself-check\b",
    r"\bsubagent context\b",
    r"\bgithub trending\b",
    r"\bgh trending\b",
    r"\btavily web search\b",
    r"\bdry[- ]run\b",
    r"心跳",
    r"自检",
    r"异常上报",
    r"任务卡住",
    r"监控",
    r"gateway",
    r"运行正常",
    r"无异常",
    r"安全检查",
    r"闲聊",
]

GENERIC_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "from",
    "openclaw",
    "memory",
    "sync",
    "记忆",
    "同步",
    "上次",
    "之前",
    "以前",
    "我们",
    "讨论",
    "问题",
    "这个",
    "那个",
    "文件",
    "系统",
    "功能",
    "内容",
    "命令",
    "执行",
    "查看",
    "现在",
    "可以",
    "需要",
    "已经",
    "进行",
    "结果",
    "使用",
    "操作",
    "context",
    "previous",
    "issue",
    "file",
    "system",
    "function",
}

STOPWORDS = GENERIC_WORDS | {word.lower() for word in TRIGGER_WORDS}

DOMAIN_PHRASES = [
    "memory-sync",
    "openclaw_memory_index",
    "openclaw",
    "obsidian",
    "github",
    "git",
    "autopilot",
    "记忆同步",
    "用进废退",
    "单一索引",
    "索引文件",
    "触发词",
    "命中冷却",
    "命中质量",
    "单一触发词",
    "关键词匹配",
    "自动驾驶",
    "版本管理",
    "每日文件",
    "永久记忆",
    "反作弊",
]

TECH_HINTS = [
    "api",
    "json",
    "yaml",
    "yml",
    "toml",
    "env",
    "md",
    "py",
    "skill",
    "index",
    "trigger",
    "github",
    "git",
    "obsidian",
    "openclaw",
    "触发",
    "冷却",
    "命中",
    "去重",
    "架构",
    "版本",
    "仓库",
]


BROAD_MATCH_KEYWORDS = {
    "api",
    "git",
    "github",
    "index",
    "json",
    "jsonl",
    "md",
    "openclaw",
    "obsidian",
    "py",
    "python",
    "skill",
    "trigger",
}

BLOCKED_KEYWORD_PATTERNS = [
    re.compile(r"(^|/)memory/\.dreams/session-corpus/", re.IGNORECASE),
    re.compile(r"(^|/)main/sessions/", re.IGNORECASE),
    re.compile(r"\.jsonl$", re.IGNORECASE),
    re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE),
    re.compile(r"^[a-z]:[\\/]", re.IGNORECASE),
    re.compile(r"[\\/].+[\\/]", re.IGNORECASE),
]

PROFILE_LABEL_BLOCKLIST = GENERIC_WORDS | BROAD_MATCH_KEYWORDS | {
    "name",
    "what",
    "to",
    "call",
    "them",
    "what to call them",
    "assistant",
    "pronouns",
    "timezone",
    "style",
    "coding style",
    "代码偏好",
    "user",
    "human",
    "you",
    "your",
    "don",
    "dont",
    "don't",
    "today",
    "yesterday",
    "tomorrow",
    "workspace",
    "rule",
    "rules",
    "note",
    "notes",
    "source",
    "sources",
    "command",
    "cmd",
    "pattern",
    "decision",
    "allow",
    "prefix_rule",
    "gateway",
    "trending",
    "review",
    "schedule",
    "scraping",
    "transcript",
    "hidden transcript",
    "memory.md",
    "memories",
    "user.md",
    "agents.md",
    "tools.md",
    "soul.md",
    "memory/yyyy-mm-dd.md",
    "关注领域",
    "github 开发者",
}

PROJECT_HINT_KEYWORDS = {
    "memory-sync",
    "agent-context",
    "context-pack",
    "openclaw",
    "obsidian",
    "codex",
    "claude",
    "opencode",
    "hermes-agent",
}

PATH_LIKE_PATTERN = re.compile(
    r"[A-Za-z]:[\\/][^\s`'\"<>|]+|[\w.-]+(?:[\\/][\w.-]+)+|[\w.-]+\.(?:py|md|json|jsonl|yaml|yml|toml|env|txt)",
    re.IGNORECASE,
)


def read_json_config(name: str) -> dict[str, Any]:
    path = ROOT / "config" / name
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Config file is invalid JSON: {path} ({exc})") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Config file must contain a JSON object: {path}")
    return data


def list_config(data: dict[str, Any], key: str) -> list[str] | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"Config key must be a list of strings: {key}")
    return value


def apply_rule_config() -> None:
    global BLACKLIST_PATTERNS, BROAD_MATCH_KEYWORDS, DOMAIN_PHRASES, GENERIC_WORDS
    global LEGACY_SOURCE_MARKERS, MIN_COMPACT_LENGTH, STOPWORDS, STRONG_KEYWORD_ALLOWLIST
    global TRIGGER_WORDS, BLOCKED_KEYWORD_PATTERNS, OPENCLAW_RECALL_MIN_SCORE
    global OPENCLAW_RECALL_MIN_RECALLS, OPENCLAW_RECALL_MAX_CANDIDATES, OPENCLAW_DREAM_MIN_CONFIDENCE

    filters = read_json_config("filters.json")
    keywords = read_json_config("keywords.json")
    triggers = read_json_config("triggers.json")

    configured = list_config(filters, "blacklist_patterns")
    if configured is not None:
        BLACKLIST_PATTERNS = configured

    configured = list_config(filters, "blocked_source_markers")
    if configured is not None:
        LEGACY_SOURCE_MARKERS = tuple(configured)

    if "min_compact_length" in filters:
        try:
            MIN_COMPACT_LENGTH = int(filters["min_compact_length"])
        except (TypeError, ValueError) as exc:
            raise ValueError("Config key must be an integer: min_compact_length") from exc

    if "openclaw_recall_min_score" in filters:
        try:
            OPENCLAW_RECALL_MIN_SCORE = float(filters["openclaw_recall_min_score"])
        except (TypeError, ValueError) as exc:
            raise ValueError("Config key must be a number: openclaw_recall_min_score") from exc

    if "openclaw_recall_min_recalls" in filters:
        try:
            OPENCLAW_RECALL_MIN_RECALLS = int(filters["openclaw_recall_min_recalls"])
        except (TypeError, ValueError) as exc:
            raise ValueError("Config key must be an integer: openclaw_recall_min_recalls") from exc

    if "openclaw_recall_max_candidates" in filters:
        try:
            OPENCLAW_RECALL_MAX_CANDIDATES = int(filters["openclaw_recall_max_candidates"])
        except (TypeError, ValueError) as exc:
            raise ValueError("Config key must be an integer: openclaw_recall_max_candidates") from exc

    if "openclaw_dream_min_confidence" in filters:
        try:
            OPENCLAW_DREAM_MIN_CONFIDENCE = float(filters["openclaw_dream_min_confidence"])
        except (TypeError, ValueError) as exc:
            raise ValueError("Config key must be a number: openclaw_dream_min_confidence") from exc

    configured = list_config(keywords, "generic_words")
    if configured is not None:
        GENERIC_WORDS = set(configured)

    configured = list_config(keywords, "broad_context_keywords")
    if configured is not None:
        BROAD_MATCH_KEYWORDS = {normalize_keyword(item) for item in configured}

    configured = list_config(keywords, "domain_phrases")
    if configured is not None:
        DOMAIN_PHRASES = configured

    configured = list_config(keywords, "strong_keyword_allowlist")
    if configured is not None:
        STRONG_KEYWORD_ALLOWLIST = {normalize_keyword(item) for item in configured}

    configured = list_config(keywords, "blocked_keyword_patterns")
    if configured is not None:
        BLOCKED_KEYWORD_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in configured]

    configured = list_config(triggers, "trigger_words")
    if configured is not None:
        TRIGGER_WORDS = configured

    STOPWORDS = GENERIC_WORDS | {word.lower() for word in TRIGGER_WORDS}


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env(ROOT / ".env")


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    if not value:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


CONFIG = {
    "OPENCLAW_WORKSPACE": os.environ.get("OPENCLAW_WORKSPACE", "~/.openclaw/workspace"),
    "VAULT_PATH": os.environ.get("OBSIDIAN_VAULT_PATH", "~/Documents/obsidian/vault"),
    "HIT_COOLDOWN_HOURS": env_int("HIT_COOLDOWN_HOURS", 24),
    "S1_TTL_MIN_DAYS": env_int("S1_TTL_MIN_DAYS", 3),
    "S1_TTL_MAX_DAYS": env_int("S1_TTL_MAX_DAYS", 10),
    "NOISE_MIN_HITS": env_int("NOISE_MIN_HITS", 5),
    "NOISE_DOMINANCE_RATIO": env_float("NOISE_DOMINANCE_RATIO", 0.8),
    "GIT_SYNC_ENABLED": env_bool("GIT_SYNC_ENABLED", False),
    "GIT_PUSH_ENABLED": env_bool("GIT_PUSH_ENABLED", True),
    "GIT_REMOTE": os.environ.get("GIT_REMOTE", "origin"),
    "GIT_BRANCH": os.environ.get("GIT_BRANCH", ""),
    "OPENCLAW_IMPORT_DISTILLED": env_bool("OPENCLAW_IMPORT_DISTILLED", True),
    "CONTEXT_EXPORT_ENABLED": env_bool("CONTEXT_EXPORT_ENABLED", True),
    "LEGACY_CONTEXT_ENABLED": env_bool("LEGACY_CONTEXT_ENABLED", False),
    "DERIVED_OUTPUTS_ENABLED": env_bool("DERIVED_OUTPUTS_ENABLED", True),
}


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def expand_path(value: str) -> Path:
    return Path(os.path.expandvars(os.path.expanduser(value))).resolve()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_summary(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        lines = len(text.splitlines())
    except OSError:
        lines = None
    return {
        "path": path.as_posix(),
        "size": path.stat().st_size,
        "sha256": file_hash(path)[:16],
        "lines": lines,
    }


def safe_name(value: str, limit: int = 80) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", value).strip(" .-")
    cleaned = re.sub(r"\s+", "-", cleaned)
    return (cleaned or "memory")[:limit]


def keyword_set(memory: dict[str, Any]) -> set[str]:
    source = memory.get("strong_keywords") or memory.get("keywords", [])
    return {normalize_keyword(str(item)) for item in source if not is_generic_keyword(str(item))}


def normalize_keyword(value: str) -> str:
    value = value.strip().strip("`*_#[]()<>:：，,。.!！?？;；")
    return re.sub(r"\s+", " ", value).lower()


def is_legacy_source(value: str | None) -> bool:
    source = str(value or "").replace("\\", "/").lower()
    return any(marker in source for marker in LEGACY_SOURCE_MARKERS)


def source_type_for(value: str | None) -> str:
    source = str(value or "").replace("\\", "/")
    if source.startswith(f"{VAULT_DAILY_DIR}/"):
        return "daily_copy"
    if source.startswith(f"{PERMANENT_DIR}/"):
        return "permanent"
    if is_legacy_source(source):
        return "legacy_session"
    return "unknown"


def openclaw_daily_source(value: str | None) -> str | None:
    source = str(value or "").replace("\\", "/")
    match = re.fullmatch(r"memory/(\d{4}-\d{2}-\d{2}\.md)", source)
    if not match:
        return None
    return f"{VAULT_DAILY_DIR}/{match.group(1)}"


def candidate_uid(origin: str, key: str, text: str = "") -> str:
    raw = f"{origin}|{key}|{text[:500]}"
    return hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:16]


def is_blocked_keyword(value: str) -> bool:
    token = normalize_keyword(value)
    if token in STRONG_KEYWORD_ALLOWLIST:
        return False
    if token in BROAD_MATCH_KEYWORDS:
        return True
    return any(pattern.search(token) for pattern in BLOCKED_KEYWORD_PATTERNS)


def scrub_blocked_keyword_text(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        token = match.group(0)
        return " " if is_blocked_keyword(token) else token

    return PATH_LIKE_PATTERN.sub(replace, text)


def is_generic_keyword(value: str) -> bool:
    token = normalize_keyword(value)
    if not token:
        return True
    if token in STRONG_KEYWORD_ALLOWLIST:
        return False
    if is_blocked_keyword(token):
        return True
    if token in STOPWORDS:
        return True
    if re.fullmatch(r"\d+", token):
        return True
    if len(token) == 1:
        return True
    if re.fullmatch(r"[\u4e00-\u9fff]{2}", token) and token not in DOMAIN_PHRASES:
        return True
    if len(token) == 2 and token in GENERIC_WORDS:
        return True
    return False


def is_low_signal_profile_label(value: str) -> bool:
    token = normalize_keyword(value)
    if not token:
        return True
    if token in PROFILE_LABEL_BLOCKLIST:
        return True
    if re.search(r"v\d+(?:\.\d+){0,2}", token):
        return True
    if re.fullmatch(r"\d{4}[./-]\d{1,2}[./-]\d{1,2}|\d{4}\.\d{1,2}\.\d{1,2}", token):
        return True
    if re.fullmatch(r"[0-9a-f]{7,}", token):
        return True
    if token not in STRONG_KEYWORD_ALLOWLIST and re.search(r"api[_-]?key|_api_|_url$|secret|token|password|passwd", token):
        return True
    if is_blocked_keyword(token):
        return True
    if re.search(r"\.(?:md|py|json|jsonl|yaml|yml|toml|env|txt)$", token):
        return True
    if "/" in token or "\\" in token:
        return True
    if token.startswith("step "):
        return True
    if re.fullmatch(r"[\W_]+", token):
        return True
    if re.fullmatch(r"[a-z]{1,2}", token):
        return True
    if re.fullmatch(r"(?:[a-z]+[\\/.-]){1,}[a-z]+", token):
        return True
    words = [word for word in re.split(r"\s+", token) if word]
    if words and all(word in PROFILE_LABEL_BLOCKLIST for word in words):
        return True
    if " " in token and token not in DOMAIN_PHRASES and not any(hint in token for hint in PROJECT_HINT_KEYWORDS):
        return True
    if len(token) > 16 and not any(hint in token for hint in PROJECT_HINT_KEYWORDS):
        return True
    if re.fullmatch(r"[\u4e00-\u9fff]{2,12}", token) and token not in DOMAIN_PHRASES:
        return True
    if len(words) > 3 and not any(hint in token for hint in PROJECT_HINT_KEYWORDS):
        return True
    return False


def canonical_glossary_label(value: str) -> str:
    token = normalize_keyword(value)
    for hint in sorted(PROJECT_HINT_KEYWORDS, key=len, reverse=True):
        if hint in token:
            return hint
    for allowed in sorted(STRONG_KEYWORD_ALLOWLIST, key=len, reverse=True):
        if allowed in token:
            return allowed
    return token


def memory_is_shared(memory: dict[str, Any]) -> bool:
    stage = str(memory.get("stage", "S1"))
    return (
        stage in {"S3", "S4"}
        or bool(memory.get("candidate_origin"))
        or int(memory.get("effective_hit_count", 0)) > 0
    )


def memory_project_label(memory: dict[str, Any]) -> str | None:
    strong = [normalize_keyword(str(item)) for item in memory.get("strong_keywords", [])]
    for token in strong:
        if token in PROJECT_HINT_KEYWORDS or token in STRONG_KEYWORD_ALLOWLIST:
            return token
    title = normalize_keyword(str(memory.get("title", "")))
    for token in PROJECT_HINT_KEYWORDS:
        if token in title:
            return token
    return None


def memory_context_title(memory: dict[str, Any]) -> str:
    title = str(memory.get("title", "Untitled memory")).strip()
    noisy_title = is_low_signal_profile_label(title) or re.search(
        r"^(发现的问题|改进建议|待办跟进|todo|review schedule|问题|建议)",
        title,
        re.IGNORECASE,
    )
    if noisy_title:
        keywords = [str(item) for item in memory.get("strong_keywords", []) if not is_low_signal_profile_label(str(item))]
        if keywords:
            return " / ".join(keywords[:4])
        title_hints = PROJECT_HINT_KEYWORDS - {"openclaw", "codex", "claude", "opencode", "hermes-agent"}
        blob = memory_blob(memory).lower()
        hinted = [hint for hint in sorted(title_hints, key=len, reverse=True) if hint in blob]
        if hinted:
            return " / ".join(hinted[:4])
    return title or "Untitled memory"


def normalized_memory_title(value: str) -> str:
    text = normalize_keyword(value)
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"[：:;；,，].*$", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


apply_rule_config()


def split_segments(content: str) -> list[tuple[str, str, str]]:
    """Return [(title, body, anchor)] from headings and horizontal rules."""
    lines = content.splitlines()
    segments: list[tuple[str, list[str], int]] = []
    current_title = ""
    current: list[str] = []
    start_line = 1

    def flush(end_line: int) -> None:
        nonlocal current, current_title, start_line
        body = "\n".join(current).strip()
        if body:
            title = current_title.strip() or first_title(body)
            segments.append((title, current[:], start_line))
        current = []
        current_title = ""
        start_line = end_line + 1

    for idx, line in enumerate(lines, start=1):
        heading = re.match(r"^\s{0,3}#{1,3}\s+(.+?)\s*$", line)
        divider = re.match(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$", line)
        if heading or divider:
            flush(idx - 1)
            if heading:
                current_title = heading.group(1).strip()
                current.append(line)
                start_line = idx
            else:
                start_line = idx + 1
            continue
        current.append(line)

    flush(len(lines))

    result: list[tuple[str, str, str]] = []
    for title, body_lines, start in segments:
        body = "\n".join(body_lines).strip()
        end = start + len(body_lines) - 1
        result.append((title, body, f"line {start}-{end}"))
    if not result and content.strip():
        result.append((first_title(content), content.strip(), f"line 1-{len(lines)}"))
    return result


def first_title(content: str) -> str:
    for line in content.splitlines():
        text = line.strip(" #\t")
        if text:
            return text[:60]
    return "Untitled memory"


def noise_reason_for_text(text: str) -> str | None:
    compact = re.sub(r"\s+", "", text)
    if len(compact) < MIN_COMPACT_LENGTH:
        return "too_short"
    return blacklist_reason_for_text(text)


def blacklist_reason_for_text(text: str) -> str | None:
    lowered = text.lower()
    for pattern in BLACKLIST_PATTERNS:
        if re.search(pattern, lowered, re.IGNORECASE):
            return f"blacklist:{pattern}"
    return None


def is_noise_segment(text: str) -> bool:
    return noise_reason_for_text(text) is not None


def memory_blob(memory: dict[str, Any]) -> str:
    return "\n".join(
        [
            str(memory.get("title", "")),
            str(memory.get("summary", "")),
            str(memory.get("excerpt", "")),
            str(memory.get("source_file", "")),
            str(memory.get("original_source_file", "")),
            " ".join(str(item) for item in memory.get("keywords", [])),
            " ".join(str(item) for item in memory.get("strong_keywords", [])),
        ]
    )


def filter_reason(memory: dict[str, Any]) -> str | None:
    source = str(memory.get("source_file", ""))
    if is_legacy_source(source):
        return "legacy_session_source"
    if source_type_for(source) == "unknown":
        return "unknown_source"
    text = memory_blob(memory)
    reason = noise_reason_for_text(text)
    if reason:
        return reason
    return None


def extract_summary(content: str, limit: int = 220) -> str:
    lines = [line.strip(" #\t-") for line in content.splitlines() if line.strip()]
    selected = " ".join(lines[:4])
    if len(selected) < 80 and len(lines) > 4:
        selected = " ".join(lines[:8])
    return selected[:limit].rstrip() + ("..." if len(selected) > limit else "")


def ingest_index_body(summary: str, source_file: str, source_anchor: str) -> str:
    return (
        f"Summary: {summary}\n\n"
        f"Original context: [[{source_file}]] {source_anchor}\n\n"
        "Policy: keep portable context compact; use source_file/source_anchor for the original record."
    )


def extract_excerpt(content: str, limit: int = 900) -> str:
    text = re.sub(r"\n{3,}", "\n\n", content.strip())
    return text[:limit].rstrip() + ("\n..." if len(text) > limit else "")


def title_from_ingest(content: str, agent: str) -> str:
    for line in content.splitlines():
        text = line.strip(" #\t-")
        if text:
            return f"{agent} handoff: {text[:70]}"
    return f"{agent} handoff {datetime.now().date().isoformat()}"


def stage_for_agent_ingest(content: str) -> str:
    lowered = content.lower()
    strong_markers = [
        "decision",
        "decided",
        "约定",
        "决定",
        "结论",
        "todo",
        "next action",
        "下一步",
        "blocker",
        "风险",
        "lesson",
        "教训",
        "handoff",
        "交接",
    ]
    if any(marker in lowered for marker in strong_markers):
        return "S2"
    return "S1"


def score_keyword(token: str, frequency: int, source: str) -> float:
    score = float(frequency)
    lowered = token.lower()
    if source in {"phrase", "code"}:
        score += 6
    if any(hint in lowered for hint in TECH_HINTS):
        score += 3
    if re.search(r"[_./\\-]", token):
        score += 2
    if len(token) >= 4:
        score += 1
    return score


def add_keyword(counter: Counter[tuple[str, str]], token: str, source: str) -> None:
    token = normalize_keyword(token)
    if is_generic_keyword(token):
        return
    counter[(token, source)] += 1


def chinese_ngrams(text: str) -> list[str]:
    tokens: list[str] = []
    for chunk in re.findall(r"[\u4e00-\u9fff]{2,24}", text):
        if chunk in STOPWORDS:
            continue
        if 4 <= len(chunk) <= 12 and not is_generic_keyword(chunk):
            tokens.append(chunk)
    return tokens


def extract_keyword_profile(content: str, title: str = "", limit: int = 16) -> dict[str, list[str]]:
    text = f"{title}\n{content}"
    keyword_text = scrub_blocked_keyword_text(text)
    counter: Counter[tuple[str, str]] = Counter()

    lowered = text.lower()
    for phrase in DOMAIN_PHRASES:
        if phrase.lower() in lowered:
            add_keyword(counter, phrase, "phrase")

    for phrase in STRONG_KEYWORD_ALLOWLIST:
        if phrase and phrase.lower() in lowered:
            add_keyword(counter, phrase, "phrase")

    for token in re.findall(r"\*\*([^*\n]{2,60})\*\*", text):
        add_keyword(counter, token, "phrase")

    for token in re.findall(r"`([^`]{2,80})`", text):
        if is_blocked_keyword(token):
            continue
        add_keyword(counter, token, "code")

    for token in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", keyword_text):
        add_keyword(counter, token, "word")

    for token in chinese_ngrams(keyword_text):
        add_keyword(counter, token, "zh")

    scored: dict[str, float] = {}
    strong: set[str] = set()
    for (token, source), frequency in counter.items():
        score = score_keyword(token, frequency, source)
        scored[token] = max(scored.get(token, 0.0), score)
        normalized = normalize_keyword(token)
        if normalized in STRONG_KEYWORD_ALLOWLIST or (
            (source in {"phrase", "code"} or score >= 5) and normalized not in BROAD_MATCH_KEYWORDS
        ):
            strong.add(token)

    ordered = [token for token, _score in sorted(scored.items(), key=lambda item: item[1], reverse=True)]
    keywords = ordered[:limit]
    strong_keywords = [token for token in keywords if token in strong][: max(6, limit // 2)]
    if not strong_keywords:
        strong_keywords = keywords[:3]
    return {"keywords": keywords, "strong_keywords": strong_keywords}


def extract_keywords(content: str, limit: int = 10) -> list[str]:
    return extract_keyword_profile(content, limit=limit)["keywords"]


def compact_text(value: str, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", value).strip()
    return text[:limit].rstrip() + ("..." if len(text) > limit else "")


def signal(category: str, label: str, weight: float, source: str, evidence: str, detail: str = "") -> dict[str, Any]:
    return {
        "category": category,
        "label": label,
        "weight": round(float(weight), 3),
        "confidence": round(min(0.99, max(0.1, float(weight))), 3),
        "source": source,
        "evidence": compact_text(evidence),
        "detail": detail,
    }


def keyword_diagnostics(text: str) -> tuple[list[str], list[str]]:
    candidates: set[str] = set()
    keyword_text = scrub_blocked_keyword_text(text)
    candidates.update(re.findall(r"`([^`]{2,80})`", text))
    candidates.update(match.group(0) for match in PATH_LIKE_PATTERN.finditer(text))
    candidates.update(re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", keyword_text))
    candidates.update(chinese_ngrams(keyword_text))

    blocked: list[str] = []
    generic: list[str] = []
    for token in sorted(candidates, key=str.lower):
        normalized = normalize_keyword(token)
        if not normalized:
            continue
        if is_blocked_keyword(normalized):
            blocked.append(token)
        elif is_generic_keyword(normalized):
            generic.append(token)
    return blocked[:20], generic[:20]


class MemoryStore:
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.index_path = vault_path / "_index" / INDEX_NAME
        self.data = self.load()

    def load(self) -> dict[str, Any]:
        if not self.index_path.exists():
            return {
                INDEX_META: {
                    "schema": "openclaw-memory-index",
                    "created_at": now_iso(),
                    "updated_at": now_iso(),
                    "processed_files": {},
                }
            }
        try:
            data = json.loads(self.index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Index file is invalid JSON: {self.index_path} ({exc})") from exc
        if INDEX_META not in data:
            data[INDEX_META] = {"schema": "openclaw-memory-index", "processed_files": {}}
        data[INDEX_META].setdefault("processed_files", {})
        processed_dates = data.pop("processed_dates", None)
        if isinstance(processed_dates, list):
            data[INDEX_META].setdefault("processed_dates", processed_dates)
        nested = data.pop("memories", None)
        if isinstance(nested, dict):
            for key, value in nested.items():
                if isinstance(value, dict) and self.is_memory_record(value):
                    data.setdefault(key, value)
        data.pop("daily_refs", None)
        data.pop("version", None)
        if "updated_at" in data:
            data[INDEX_META].setdefault("updated_at", data.pop("updated_at"))
        for value in data.values():
            if isinstance(value, dict) and self.is_memory_record(value):
                self.ensure_keyword_profile(value)
        return self.normalize_record_ids(data)

    @staticmethod
    def normalize_record_ids(data: dict[str, Any]) -> dict[str, Any]:
        records: list[tuple[str, dict[str, Any]]] = []
        passthrough: dict[str, Any] = {INDEX_META: data.get(INDEX_META, {})}
        for key, value in data.items():
            if key == INDEX_META:
                continue
            if isinstance(value, dict) and MemoryStore.is_memory_record(value):
                records.append((key, value))
            elif key not in RESERVED_INDEX_KEYS:
                passthrough[key] = value

        def record_sort_key(item: tuple[str, dict[str, Any]]) -> tuple[int, int | str]:
            key = item[0]
            match = re.match(r"memory_(\d+)$", key)
            if match:
                return (0, int(match.group(1)))
            return (1, key)

        normalized = {INDEX_META: passthrough.get(INDEX_META, {})}
        for index, (old_key, memory) in enumerate(sorted(records, key=record_sort_key), start=1):
            new_key = f"memory_{index:03d}"
            if old_key != new_key:
                memory.setdefault("legacy_id", old_key)
            normalized[new_key] = memory
        for key, value in passthrough.items():
            if key != INDEX_META:
                normalized[key] = value
        return normalized

    @staticmethod
    def is_memory_record(value: dict[str, Any]) -> bool:
        return any(field in value for field in ("title", "summary", "keywords", "source_file"))

    @staticmethod
    def ensure_keyword_profile(memory: dict[str, Any]) -> None:
        memory.setdefault("source_type", source_type_for(memory.get("source_file")))
        memory.setdefault("quality_score", 1.0)
        memory.setdefault("filtered_reason", None)
        if memory.get("strong_keywords"):
            memory["keywords"] = [kw for kw in memory.get("keywords", []) if not is_generic_keyword(str(kw))][:18]
            memory["strong_keywords"] = [
                kw for kw in memory.get("strong_keywords", []) if not is_generic_keyword(str(kw))
            ][:10]
            return
        MemoryStore.refresh_keyword_profile(memory)

    @staticmethod
    def refresh_keyword_profile(memory: dict[str, Any]) -> None:
        text = "\n".join(
            [
                str(memory.get("summary", "")),
                str(memory.get("excerpt", "")),
            ]
        )
        profile = extract_keyword_profile(text, title=str(memory.get("title", "")))
        memory["keywords"] = profile["keywords"]
        memory["strong_keywords"] = profile["strong_keywords"]
        memory["source_type"] = source_type_for(memory.get("source_file"))
        memory.setdefault("quality_score", 1.0)
        memory.setdefault("filtered_reason", None)

    def memories(self) -> dict[str, dict[str, Any]]:
        return {
            k: v
            for k, v in self.data.items()
            if k not in RESERVED_INDEX_KEYS and isinstance(v, dict) and self.is_memory_record(v)
        }

    def save(self) -> None:
        self.data[INDEX_META]["updated_at"] = now_iso()
        self.data.pop("memories", None)
        self.data.pop("daily_refs", None)
        self.data.pop("processed_dates", None)
        self.data.pop("version", None)
        if "updated_at" in self.data:
            self.data[INDEX_META].setdefault("legacy_updated_at", self.data.pop("updated_at"))
        self.data = self.normalize_record_ids(self.data)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.index_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.index_path)

    def next_id(self) -> str:
        max_id = 0
        for key in self.memories():
            match = re.match(r"memory_(\d+)$", key)
            if match:
                max_id = max(max_id, int(match.group(1)))
        return f"memory_{max_id + 1:03d}"

    def capacity_factor(self) -> float:
        long_count = sum(1 for memory in self.memories().values() if memory.get("stage") in {"S2", "S3", "S4"})
        size_kb = self.index_path.stat().st_size / 1024 if self.index_path.exists() else 0
        if long_count > 50 or size_kb > 150:
            return 0.0
        if long_count < 20 or size_kb < 50:
            return 1.0
        return 0.5

    def ttl_days(self, stage: str) -> int | None:
        if stage == "S4":
            return None
        factor = self.capacity_factor()
        ranges = {
            "S1": (CONFIG["S1_TTL_MIN_DAYS"], CONFIG["S1_TTL_MAX_DAYS"]),
            "S2": (7, 15),
            "S3": (14, 30),
        }
        low, high = ranges.get(stage, ranges["S1"])
        return int(round(low + (high - low) * factor))

    def expire_at(self, stage: str, quality: float = 1.0) -> str | None:
        ttl = self.ttl_days(stage)
        if ttl is None:
            return None
        return (datetime.now() + timedelta(days=max(1, ttl * quality))).replace(microsecond=0).isoformat()

    def referenced_files(self) -> set[str]:
        refs: set[str] = set()
        for memory in self.memories().values():
            if memory.get("source_file"):
                refs.add(str(memory["source_file"]).replace("\\", "/"))
            for source in memory.get("sources", []):
                if source.get("file"):
                    refs.add(str(source["file"]).replace("\\", "/"))
        return refs


class MemorySync:
    def __init__(self):
        self.openclaw_path = expand_path(CONFIG["OPENCLAW_WORKSPACE"])
        self.vault_path = expand_path(CONFIG["VAULT_PATH"])
        self.store = MemoryStore(self.vault_path)

    def log(self, message: str) -> None:
        print(message)

    def source_rel(self, path: Path) -> str:
        try:
            return path.relative_to(self.openclaw_path).as_posix()
        except ValueError:
            return path.as_posix()

    def vault_rel(self, path: Path) -> str:
        try:
            return path.relative_to(self.vault_path).as_posix()
        except ValueError:
            return path.as_posix()

    def vault_daily_path(self, original_path: Path) -> Path:
        return self.vault_path / VAULT_DAILY_DIR / original_path.name

    def sync_daily_copy(self, original_path: Path, text: str) -> Path:
        copy_path = self.vault_daily_path(original_path)
        copy_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = copy_path.with_suffix(copy_path.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, copy_path)
        self.log(f"COPY daily file to vault: {self.vault_rel(copy_path)}")
        return copy_path

    def build_memory(
        self,
        title: str,
        body: str,
        source_file: str,
        anchor: str,
        original_source_file: str,
    ) -> dict[str, Any]:
        created = now_iso()
        stage = "S1"
        summary = extract_summary(body)
        keyword_profile = extract_keyword_profile(body, title=title)
        return {
            "title": title[:100],
            "summary": summary,
            "keywords": keyword_profile["keywords"],
            "strong_keywords": keyword_profile["strong_keywords"],
            "stage": stage,
            "source_type": source_type_for(source_file),
            "quality_score": 1.0,
            "filtered_reason": None,
            "source_file": source_file,
            "source_anchor": anchor,
            "original_source_file": original_source_file,
            "excerpt": extract_excerpt(body),
            "created_at": created,
            "last_hit_at": None,
            "last_effective_hit_at": None,
            "raw_hit_count": 0,
            "effective_hit_count": 0,
            "expire_at": self.store.expire_at(stage),
            "hit_distribution": {word: 0 for word in TRIGGER_WORDS},
            "noise_score": 0,
            "merged_from": [],
            "sources": [
                {
                    "file": source_file,
                    "anchor": anchor,
                    "original_file": original_source_file,
                    "created_at": created,
                }
            ],
        }

    def build_distilled_memory(
        self,
        title: str,
        body: str,
        source_file: str,
        anchor: str,
        original_source_file: str,
        origin: str,
        stage: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        memory = self.build_memory(title, body, source_file, anchor, original_source_file)
        memory["stage"] = stage
        memory["expire_at"] = self.store.expire_at(stage)
        memory["candidate_origin"] = origin
        memory["candidate_uid"] = metadata.get("candidate_uid") or candidate_uid(origin, metadata.get("openclaw_key", ""), body)
        memory["source_type"] = "openclaw_distilled"
        memory["quality_score"] = float(metadata.get("quality_score", 1.0))
        memory.update(metadata)
        memory["sources"][0]["candidate_origin"] = origin
        return memory

    def build_agent_ingest_memory(
        self,
        agent: str,
        title: str,
        body: str,
        source_file: str,
        anchor: str,
    ) -> dict[str, Any]:
        stage = stage_for_agent_ingest(body)
        memory = self.build_memory(title, body, source_file, anchor, source_file)
        memory["stage"] = stage
        memory["expire_at"] = self.store.expire_at(stage)
        memory["source_agent"] = agent
        memory["source_type"] = "agent_ingest"
        memory["candidate_origin"] = f"{agent}-ingest"
        memory["candidate_uid"] = candidate_uid(f"{agent}-ingest", source_file, body)
        memory["memory_lane"] = "pending"
        memory["source_confidence"] = "agent_submitted"
        memory["quality_score"] = 0.8 if stage == "S2" else 0.65
        memory["context_storage_policy"] = "summary_with_source_link"
        memory["original_context_file"] = source_file
        memory["original_context_anchor"] = anchor
        memory["sources"][0]["candidate_origin"] = memory["candidate_origin"]
        memory["sources"][0]["agent"] = agent
        return memory

    def stage_for_openclaw_candidate(self, metadata: dict[str, Any], default: str = "S1") -> str:
        origin = str(metadata.get("candidate_origin", ""))
        if origin == "openclaw-promoted-memory":
            return "S4"
        if origin in {"openclaw-deep", "openclaw-rem"}:
            return "S3"
        score = float(metadata.get("openclaw_score") or 0)
        recalls = int(metadata.get("openclaw_recall_count") or 0)
        grounded = int(metadata.get("openclaw_grounded_count") or 0)
        rem_hits = int(metadata.get("openclaw_rem_hits") or 0)
        if rem_hits > 0 or grounded > 0 or recalls >= 2 or score >= 0.82:
            return "S3"
        if recalls >= 1 or score >= OPENCLAW_RECALL_MIN_SCORE:
            return "S2"
        return default

    def find_duplicate(self, candidate: dict[str, Any]) -> tuple[str, dict[str, Any], float] | None:
        candidate_keywords = keyword_set(candidate)
        candidate_title = normalized_memory_title(str(candidate.get("title", "")))
        best: tuple[str, dict[str, Any], float] | None = None
        for memory_id, memory in self.store.memories().items():
            memory_title = normalized_memory_title(str(memory.get("title", "")))
            score = jaccard(candidate_keywords, keyword_set(memory))
            if candidate_title and candidate_title == memory_title and not is_low_signal_profile_label(candidate_title):
                score = max(score, 0.95)
            if score >= 0.60 and (best is None or score > best[2]):
                best = (memory_id, memory, score)
        return best

    def merge_memory(self, memory_id: str, existing: dict[str, Any], candidate: dict[str, Any], score: float) -> None:
        source = {
            "file": candidate["source_file"],
            "anchor": candidate["source_anchor"],
            "original_file": candidate.get("original_source_file"),
            "created_at": now_iso(),
        }
        sources = existing.setdefault("sources", [])
        if source["file"] not in {item.get("file") for item in sources}:
            sources.append(source)

        existing["merged_from"] = sorted(set(existing.get("merged_from", []) + [candidate["source_file"]]))
        existing["keywords"] = list(dict.fromkeys(existing.get("keywords", []) + candidate.get("keywords", [])))[:18]
        existing["strong_keywords"] = list(
            dict.fromkeys(existing.get("strong_keywords", []) + candidate.get("strong_keywords", []))
        )[:10]
        existing["summary"] = candidate["summary"]
        existing["excerpt"] = candidate["excerpt"]
        existing["source_file"] = candidate["source_file"]
        existing["source_anchor"] = candidate["source_anchor"]
        existing["original_source_file"] = candidate.get("original_source_file")
        for field in (
            "candidate_origin",
            "candidate_uid",
            "openclaw_key",
            "openclaw_score",
            "openclaw_max_score",
            "openclaw_recall_count",
            "openclaw_daily_count",
            "openclaw_grounded_count",
            "openclaw_light_hits",
            "openclaw_rem_hits",
                "openclaw_concept_tags",
                "openclaw_confidence",
                "context_storage_policy",
                "original_context_file",
                "original_context_anchor",
            ):
            if field in candidate:
                existing[field] = candidate[field]
        if candidate.get("stage") == "S4" or STAGES.index(candidate.get("stage", "S1")) > STAGES.index(existing.get("stage", "S1")):
            existing["stage"] = candidate.get("stage", existing.get("stage", "S1"))
            existing["expire_at"] = self.store.expire_at(existing["stage"])
        existing["updated_at"] = now_iso()
        self.log(f"MERGE {candidate['source_file']} -> {memory_id} keyword_overlap={score:.2f}")

    def add_or_merge(self, candidate: dict[str, Any]) -> str:
        uid = candidate.get("candidate_uid")
        if uid:
            for memory_id, existing in self.store.memories().items():
                if existing.get("candidate_uid") == uid:
                    self.merge_memory(memory_id, existing, candidate, 1.0)
                    return memory_id
        duplicate = self.find_duplicate(candidate)
        if duplicate:
            memory_id, existing, score = duplicate
            self.merge_memory(memory_id, existing, candidate, score)
            return memory_id
        memory_id = self.store.next_id()
        self.store.data[memory_id] = candidate
        self.log(f"ADD {memory_id}: {candidate['title']}")
        return memory_id

    def ensure_vault_copy_for_source(self, source: str) -> str | None:
        vault_source = openclaw_daily_source(source)
        if not vault_source:
            return None
        original = self.openclaw_path / source
        if not original.exists():
            return None
        copy_path = self.vault_path / vault_source
        if original.exists() and not copy_path.exists():
            text = original.read_text(encoding="utf-8", errors="replace")
            self.sync_daily_copy(original, text)
        return vault_source

    def collect_recall_candidates(self) -> list[dict[str, Any]]:
        recall_path = self.openclaw_path / "memory" / ".dreams" / "short-term-recall.json"
        phase_path = self.openclaw_path / "memory" / ".dreams" / "phase-signals.json"
        if not recall_path.exists():
            return []
        try:
            recall_data = json.loads(recall_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            self.log(f"SKIP OpenClaw recall import: invalid JSON {self.source_rel(recall_path)}")
            return []
        try:
            phase_data = json.loads(phase_path.read_text(encoding="utf-8")) if phase_path.exists() else {}
        except json.JSONDecodeError:
            phase_data = {}

        entries = recall_data.get("entries", {})
        phases = phase_data.get("entries", {}) if isinstance(phase_data, dict) else {}
        if not isinstance(entries, dict):
            return []

        selected: list[tuple[float, dict[str, Any]]] = []
        for key, entry in entries.items():
            if not isinstance(entry, dict):
                continue
            source = str(entry.get("path") or "")
            vault_source = self.ensure_vault_copy_for_source(source)
            if not vault_source:
                continue
            snippet = str(entry.get("snippet") or "").strip()
            if not snippet or noise_reason_for_text(snippet):
                continue
            phase = phases.get(key, {}) if isinstance(phases, dict) else {}
            score = float(entry.get("totalScore") or 0)
            recalls = int(entry.get("recallCount") or 0)
            grounded = int(entry.get("groundedCount") or 0)
            rem_hits = int(phase.get("remHits") or 0) if isinstance(phase, dict) else 0
            if score < OPENCLAW_RECALL_MIN_SCORE and recalls < OPENCLAW_RECALL_MIN_RECALLS and grounded == 0 and rem_hits == 0:
                continue

            start = int(entry.get("startLine") or 1)
            end = int(entry.get("endLine") or start)
            tags = [str(item) for item in entry.get("conceptTags", []) if isinstance(item, str)]
            body = snippet
            if tags:
                body = f"{snippet}\n\nTags: {', '.join(tags[:12])}"
            metadata = {
                "candidate_origin": "openclaw-short-term-recall",
                "candidate_uid": candidate_uid("openclaw-short-term-recall", str(key), snippet),
                "openclaw_key": str(key),
                "openclaw_score": score,
                "openclaw_max_score": float(entry.get("maxScore") or score),
                "openclaw_recall_count": recalls,
                "openclaw_daily_count": int(entry.get("dailyCount") or 0),
                "openclaw_grounded_count": grounded,
                "openclaw_light_hits": int(phase.get("lightHits") or 0) if isinstance(phase, dict) else 0,
                "openclaw_rem_hits": rem_hits,
                "openclaw_concept_tags": tags[:20],
                "quality_score": min(1.0, max(0.7, score)),
            }
            stage = self.stage_for_openclaw_candidate(metadata)
            candidate = self.build_distilled_memory(
                first_title(snippet),
                body,
                vault_source,
                f"line {start}-{end}",
                source,
                "openclaw-short-term-recall",
                stage,
                metadata,
            )
            selected.append((score + recalls + grounded + rem_hits, candidate))

        selected.sort(key=lambda item: item[0], reverse=True)
        return [candidate for _score, candidate in selected[:OPENCLAW_RECALL_MAX_CANDIDATES]]

    def collect_dream_candidates(self, folder: str, origin: str) -> list[dict[str, Any]]:
        dream_dir = self.openclaw_path / "memory" / "dreaming" / folder
        if not dream_dir.exists():
            return []
        candidates: list[dict[str, Any]] = []
        pattern = re.compile(r"\[confidence=([0-9.]+)\s+evidence=([^\]]+)\]")
        for path in sorted(dream_dir.glob("*.md"))[-7:]:
            text = path.read_text(encoding="utf-8", errors="replace")
            for line_no, line in enumerate(text.splitlines(), start=1):
                match = pattern.search(line)
                if not match:
                    continue
                confidence = float(match.group(1))
                evidence = match.group(2).strip()
                if confidence < OPENCLAW_DREAM_MIN_CONFIDENCE:
                    continue
                evidence_match = re.match(r"(memory/\d{4}-\d{2}-\d{2}\.md):(\d+)(?:-(\d+))?", evidence)
                if not evidence_match:
                    continue
                source = evidence_match.group(1)
                start = evidence_match.group(2)
                end = evidence_match.group(3) or start
                vault_source = self.ensure_vault_copy_for_source(source)
                if not vault_source:
                    continue
                body = pattern.sub("", line).lstrip("- ").strip()
                if not body or blacklist_reason_for_text(body):
                    continue
                metadata = {
                    "candidate_origin": origin,
                    "candidate_uid": candidate_uid(origin, f"{path.name}:{line_no}:{evidence}", body),
                    "openclaw_confidence": confidence,
                    "openclaw_evidence": evidence,
                    "quality_score": confidence,
                }
                stage = self.stage_for_openclaw_candidate(metadata, default="S2")
                candidates.append(
                    self.build_distilled_memory(
                        first_title(body),
                        body,
                        vault_source,
                        f"line {start}-{end}",
                        source,
                        origin,
                        stage,
                        metadata,
                    )
                )
        return candidates

    def collect_promoted_candidates(self) -> list[dict[str, Any]]:
        memory_path = self.openclaw_path / "MEMORY.md"
        if not memory_path.exists():
            return []
        lines = memory_path.read_text(encoding="utf-8", errors="replace").splitlines()
        candidates: list[dict[str, Any]] = []
        for index, line in enumerate(lines):
            marker = re.search(r"openclaw-memory-promotion:([^ ]+)", line)
            if not marker:
                continue
            body = lines[index + 1].strip("- ").strip() if index + 1 < len(lines) else marker.group(1)
            source_match = re.search(r"source=(memory/\d{4}-\d{2}-\d{2}\.md):(\d+)-(\d+)", body)
            if not source_match or blacklist_reason_for_text(body):
                continue
            source = source_match.group(1)
            vault_source = self.ensure_vault_copy_for_source(source)
            if not vault_source:
                continue
            score_match = re.search(r"score=([0-9.]+)", body)
            metadata = {
                "candidate_origin": "openclaw-promoted-memory",
                "candidate_uid": candidate_uid("openclaw-promoted-memory", marker.group(1), body),
                "openclaw_key": marker.group(1),
                "openclaw_score": float(score_match.group(1)) if score_match else 1.0,
                "quality_score": 1.0,
            }
            candidates.append(
                self.build_distilled_memory(
                    first_title(body),
                    body,
                    vault_source,
                    f"line {source_match.group(2)}-{source_match.group(3)}",
                    source,
                    "openclaw-promoted-memory",
                    "S4",
                    metadata,
                )
            )
        return candidates

    def import_openclaw_distilled_candidates(self) -> int:
        if not CONFIG["OPENCLAW_IMPORT_DISTILLED"]:
            return 0
        candidates: list[dict[str, Any]] = []
        candidates.extend(self.collect_promoted_candidates())
        candidates.extend(self.collect_dream_candidates("deep", "openclaw-deep"))
        candidates.extend(self.collect_dream_candidates("rem", "openclaw-rem"))
        candidates.extend(self.collect_recall_candidates())

        changed = 0
        for candidate in candidates:
            self.add_or_merge(candidate)
            changed += 1
        if changed:
            self.store.data[INDEX_META]["openclaw_distilled_imported_at"] = now_iso()
            self.store.data[INDEX_META]["openclaw_distilled_imported_count"] = changed
        self.log(f"OpenClaw distilled import: candidates={changed}")
        return changed

    def cmd_sync(self) -> int:
        memory_dir = self.openclaw_path / DAILY_DIR
        if not memory_dir.exists():
            self.log(f"ERROR memory directory not found: {memory_dir}")
            return 1

        processed = self.store.data[INDEX_META].setdefault("processed_files", {})
        referenced = self.store.referenced_files()
        changed_files = 0
        created_or_merged = 0
        unrelated_files: list[Path] = []

        for path in sorted(memory_dir.glob("*.md")):
            original_rel = self.source_rel(path)
            copy_path = self.vault_daily_path(path)
            copy_rel = self.vault_rel(copy_path)
            digest = file_hash(path)
            if processed.get(original_rel) == digest and (copy_path.exists() or copy_rel not in referenced):
                continue
            changed_files += 1
            text = path.read_text(encoding="utf-8", errors="replace")
            copy_path = self.sync_daily_copy(path, text)
            candidates: list[dict[str, Any]] = []
            for title, body, anchor in split_segments(text):
                reason = noise_reason_for_text(body)
                if reason:
                    self.log(f"SKIP segment reason={reason}: {copy_rel} {anchor} {title[:60]}")
                    continue
                candidates.append(self.build_memory(title, body, copy_rel, anchor, original_rel))

            if not candidates:
                unrelated_files.append(copy_path)
                processed[original_rel] = digest
                self.log(f"MARK daily copy for cleanup check reason=no_indexable_segments: {copy_rel}")
                continue

            for candidate in candidates:
                self.add_or_merge(candidate)
                created_or_merged += 1
            processed[original_rel] = digest

        created_or_merged += self.import_openclaw_distilled_candidates()
        expired = self.apply_expiry()
        cleaned = self.clean_unrelated_daily_files(unrelated_files)
        changed = changed_files > 0 or created_or_merged > 0 or expired or cleaned
        if changed:
            self.store.save()
        self.write_obsidian_index()
        if CONFIG["DERIVED_OUTPUTS_ENABLED"]:
            self.refresh_derived_outputs()

        self.log(f"Sync complete: files={changed_files}, memories={created_or_merged}")
        return 0

    def clean_unrelated_daily_files(self, candidates: list[Path]) -> bool:
        referenced = self.store.referenced_files()
        changed = False
        for path in candidates:
            rel = self.vault_rel(path)
            if rel in referenced:
                continue
            if path.exists():
                path.unlink()
                changed = True
            self.log(f"REMOVED unrelated vault daily copy reason=no_indexed_memory: {rel}")
        return changed

    def apply_expiry(self) -> bool:
        now = datetime.now()
        to_delete: list[str] = []
        changed = False
        for memory_id, memory in self.store.memories().items():
            stage = memory.get("stage", "S1")
            if stage == "S4":
                continue
            expire_at = parse_time(memory.get("expire_at"))
            if not expire_at or expire_at > now:
                continue
            if stage == "S1":
                to_delete.append(memory_id)
                self.log(f"EXPIRE remove {memory_id}: {memory.get('title')}")
                changed = True
            else:
                new_stage = PREVIOUS_STAGE.get(stage, "S1")
                memory["stage"] = new_stage
                memory["expire_at"] = self.store.expire_at(new_stage)
                memory["updated_at"] = now_iso()
                self.log(f"EXPIRE downgrade {memory_id}: {stage} -> {new_stage}")
                changed = True
        for memory_id in to_delete:
            self.store.data.pop(memory_id, None)
        return changed

    def cmd_search(self, query: str) -> int:
        query_lower = query.lower()
        terms = [normalize_keyword(term) for term in re.split(r"\s+", query_lower) if not is_generic_keyword(term)]
        if not terms:
            terms = [query_lower]
        results: list[tuple[int, str, dict[str, Any]]] = []
        for memory_id, memory in self.store.memories().items():
            haystack = " ".join(
                [
                    str(memory.get("title", "")),
                    str(memory.get("summary", "")),
                    str(memory.get("excerpt", "")),
                    " ".join(memory.get("keywords", [])),
                    " ".join(memory.get("strong_keywords", [])),
                ]
            ).lower()
            score = sum(5 for kw in memory.get("strong_keywords", []) if query_lower in str(kw).lower())
            score += sum(2 for kw in memory.get("keywords", []) if query_lower in str(kw).lower())
            score += sum(1 for term in terms if term and term in haystack)
            if score:
                results.append((score, memory_id, memory))
        results.sort(key=lambda item: item[0], reverse=True)

        self.log(f"Search results: {len(results)}")
        for score, memory_id, memory in results[:10]:
            self.log(f"- {memory_id} [{memory.get('stage')}] score={score} {memory.get('title')}")
            self.log(f"  {memory.get('summary', '')}")
        return 0

    def trigger_words_in(self, text: str) -> list[str]:
        lowered = text.lower()
        return [word for word in TRIGGER_WORDS if word.lower() in lowered]

    def matching_memories(self, text: str) -> list[tuple[str, dict[str, Any], float, list[str]]]:
        lowered = text.lower()
        matches: list[tuple[str, dict[str, Any], float, list[str]]] = []
        for memory_id, memory in self.store.memories().items():
            keywords = [str(item) for item in memory.get("keywords", []) if not is_generic_keyword(str(item))]
            strong_keywords = [
                str(item) for item in memory.get("strong_keywords", []) if not is_generic_keyword(str(item))
            ]
            matched_strong = [kw for kw in strong_keywords if kw.lower() in lowered]
            matched_general = [kw for kw in keywords if kw.lower() in lowered and kw not in matched_strong]
            matched_specific = [kw for kw in matched_strong if normalize_keyword(kw) not in BROAD_MATCH_KEYWORDS]
            title = str(memory.get("title", "")).lower()
            summary = str(memory.get("summary", "")).lower()
            title_hit = bool(title and len(title) > 5 and title in lowered)
            summary_hit = any(kw.lower() in summary for kw in matched_specific)

            if len(matched_specific) >= 3:
                quality = 1.0
            elif len(matched_specific) >= 2:
                quality = 0.85
            elif len(matched_specific) == 1 and (
                title_hit or summary_hit or len(matched_general) + len(matched_strong) - len(matched_specific) >= 2
            ):
                quality = 0.7
            else:
                continue
            matches.append((memory_id, memory, quality, matched_strong + matched_general[:3]))
        matches.sort(key=lambda item: item[2], reverse=True)
        return matches

    def cmd_trigger_check(self, text: str) -> int:
        triggers = self.trigger_words_in(text)
        self.log(f"Trigger words: {', '.join(triggers) if triggers else '(none)'}")
        if not triggers:
            return 0
        matches = self.matching_memories(text)
        self.log(f"Matched memories: {len(matches)}")
        for memory_id, memory, quality, matched in matches[:10]:
            self.log(f"- {memory_id} quality={quality:.2f} {memory.get('title')}")
            self.log(f"  keywords: {', '.join(matched) if matched else '(title match)'}")
        return 0

    def cmd_diagnose(self, text: str) -> int:
        triggers = self.trigger_words_in(text)
        reason = noise_reason_for_text(text)
        profile = extract_keyword_profile(text)
        blocked, generic = keyword_diagnostics(text)
        matches = self.matching_memories(text)

        self.log(f"Trigger words: {', '.join(triggers) if triggers else '(none)'}")
        self.log(f"Filtered: {'yes' if reason else 'no'}")
        if reason:
            self.log(f"Filter reason: {reason}")
        self.log(f"Keywords: {', '.join(profile['keywords']) if profile['keywords'] else '(none)'}")
        self.log(
            f"Strong keywords: {', '.join(profile['strong_keywords']) if profile['strong_keywords'] else '(none)'}"
        )
        self.log(f"Blocked keyword candidates: {', '.join(blocked) if blocked else '(none)'}")
        self.log(f"Generic keyword candidates: {', '.join(generic) if generic else '(none)'}")
        self.log(f"Matched memories: {len(matches)}")
        for memory_id, memory, quality, matched in matches[:10]:
            self.log(f"- {memory_id} quality={quality:.2f} {memory.get('title')}")
            self.log(f"  matched: {', '.join(matched) if matched else '(title match)'}")
        return 0

    def cmd_trigger_hit(self, text: str) -> int:
        triggers = self.trigger_words_in(text)
        if not triggers:
            self.log("No trigger word found; no hit recorded.")
            return 0

        matches = self.matching_memories(text)
        if not matches:
            self.log("Trigger found, but no indexed memory matched.")
            return 0

        now = datetime.now()
        cooldown = timedelta(hours=CONFIG["HIT_COOLDOWN_HOURS"])
        changed = 0

        for memory_id, memory, quality, matched in matches:
            memory["raw_hit_count"] = int(memory.get("raw_hit_count", 0)) + 1
            memory["last_hit_at"] = now_iso()
            distribution = memory.setdefault("hit_distribution", {word: 0 for word in TRIGGER_WORDS})
            for trigger in triggers:
                distribution[trigger] = int(distribution.get(trigger, 0)) + 1

            last_effective = parse_time(memory.get("last_effective_hit_at"))
            if last_effective and now - last_effective < cooldown:
                self.log(f"COOLDOWN raw hit only: {memory_id}")
                changed += 1
                continue

            memory["effective_hit_count"] = int(memory.get("effective_hit_count", 0)) + 1
            memory["last_effective_hit_at"] = now_iso()

            noisy = self.apply_noise_rule(memory_id, memory)
            if not noisy:
                self.promote_if_needed(memory_id, memory, quality)
            changed += 1
            self.log(f"HIT {memory_id} quality={quality:.2f} keywords={', '.join(matched)}")

        self.store.save()
        self.write_obsidian_index()
        self.write_obsidian_surfaces()
        self.log(f"Trigger hit complete: changed={changed}")
        return 0

    def apply_noise_rule(self, memory_id: str, memory: dict[str, Any]) -> bool:
        distribution = memory.get("hit_distribution", {})
        total = sum(int(value) for value in distribution.values())
        if total < CONFIG["NOISE_MIN_HITS"]:
            return False
        trigger, count = max(distribution.items(), key=lambda item: int(item[1]))
        if count / max(1, total) < CONFIG["NOISE_DOMINANCE_RATIO"]:
            return False

        stage = memory.get("stage", "S1")
        memory["noise_score"] = int(memory.get("noise_score", 0)) + 1
        if stage == "S1":
            self.store.data.pop(memory_id, None)
            self.log(f"NOISE remove {memory_id}: dominated by trigger '{trigger}'")
        else:
            new_stage = PREVIOUS_STAGE.get(stage, "S1")
            memory["stage"] = new_stage
            memory["expire_at"] = self.store.expire_at(new_stage, 0.7)
            memory["updated_at"] = now_iso()
            self.log(f"NOISE downgrade {memory_id}: {stage} -> {new_stage}")
        return True

    def promote_if_needed(self, memory_id: str, memory: dict[str, Any], quality: float) -> None:
        hits = int(memory.get("effective_hit_count", 0))
        current = memory.get("stage", "S1")
        target = current
        if hits >= 3:
            target = "S4"
        elif hits >= 2:
            target = "S3"
        elif hits >= 1:
            target = "S2"

        if STAGES.index(target) > STAGES.index(current):
            memory["stage"] = target
            self.log(f"PROMOTE {memory_id}: {current} -> {target}")

        memory["expire_at"] = self.store.expire_at(memory["stage"], quality)
        memory["updated_at"] = now_iso()

        if memory["stage"] == "S4" and not memory.get("permanent_file"):
            self.extract_permanent_memory(memory_id, memory)

    def extract_permanent_memory(self, memory_id: str, memory: dict[str, Any]) -> None:
        relative = f"{PERMANENT_DIR}/{memory_id}-{safe_name(memory.get('title', 'memory'))}.md"
        memory["permanent_file"] = relative
        path = self.vault_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        sources = "\n".join(f"- {item.get('file')} {item.get('anchor', '')}" for item in memory.get("sources", []))
        content = (
            f"# {memory.get('title')}\n\n"
            f"{memory.get('summary', '')}\n\n"
            "## Keywords\n\n"
            + ", ".join(memory.get("keywords", []))
            + "\n\n## Excerpt\n\n"
            + memory.get("excerpt", "")
            + "\n\n## Sources\n\n"
            + sources
            + "\n"
        )
        path.write_text(content, encoding="utf-8")

    def write_obsidian_index(self) -> bool:
        path = self.vault_path / OBSIDIAN_INDEX_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        memories = self.store.memories()
        counts = Counter(memory.get("stage", "S1") for memory in memories.values())
        updated_at = self.store.data.get(INDEX_META, {}).get("updated_at") or now_iso()
        lines = [
            "# OpenClaw 记忆索引",
            "",
            "> 自动生成文件。脚本使用 `_index/openclaw_memory_index.json` 作为机器真相源，本文件作为 Obsidian 可读入口。",
            "",
            f"- 更新时间：{updated_at}",
            f"- 记忆总数：{len(memories)}",
            f"- 阶段分布：S1={counts.get('S1', 0)}，S2={counts.get('S2', 0)}，S3={counts.get('S3', 0)}，S4={counts.get('S4', 0)}",
            "",
        ]
        for stage in STAGES:
            stage_items = [
                (memory_id, memory)
                for memory_id, memory in memories.items()
                if memory.get("stage", "S1") == stage
            ]
            lines.extend([f"## {stage}", ""])
            if not stage_items:
                lines.extend(["_暂无_", ""])
                continue
            for memory_id, memory in sorted(stage_items, key=lambda item: str(item[1].get("title", ""))):
                title = str(memory.get("title", "Untitled memory")).replace("\n", " ")
                summary = str(memory.get("summary", "")).replace("\n", " ")
                keywords = ", ".join(str(item) for item in memory.get("strong_keywords") or memory.get("keywords", [])[:6])
                source = str(memory.get("source_file", ""))
                expire_at = memory.get("expire_at") or "permanent"
                lines.append(f"### {memory_id} - {title}")
                lines.append("")
                if summary:
                    lines.append(summary)
                    lines.append("")
                lines.append(f"- 阶段：{memory.get('stage', 'S1')}")
                lines.append(f"- 有效命中：{memory.get('effective_hit_count', 0)}")
                if memory.get("candidate_origin"):
                    lines.append(f"- OpenClaw candidate：{memory.get('candidate_origin')}")
                if memory.get("openclaw_score") is not None:
                    lines.append(f"- OpenClaw score：{memory.get('openclaw_score')}")
                if memory.get("openclaw_confidence") is not None:
                    lines.append(f"- OpenClaw confidence：{memory.get('openclaw_confidence')}")
                lines.append(f"- 过期时间：{expire_at}")
                if keywords:
                    lines.append(f"- 关键词：{keywords}")
                if source:
                    lines.append(f"- 来源：[[{source}]]")
                if memory.get("permanent_file"):
                    lines.append(f"- 永久文件：[[{memory['permanent_file']}]]")
                lines.append("")
        content = "\n".join(lines).rstrip() + "\n"
        if path.exists() and path.read_text(encoding="utf-8") == content:
            return False
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)
        return True

    def memory_page_rel(self, memory_id: str, memory: dict[str, Any]) -> str:
        return f"{MEMORY_PAGES_DIR}/{memory_id}-{safe_name(str(memory.get('title', 'memory')), 56)}.md"

    def yaml_scalar(self, value: Any) -> str:
        text = str(value or "").replace("\\", "/").replace('"', '\\"')
        return f'"{text}"'

    def yaml_list(self, values: list[Any]) -> list[str]:
        items = [str(item).strip() for item in values if str(item).strip()]
        if not items:
            return ["[]"]
        return [f"- {self.yaml_scalar(item)}" for item in items[:12]]

    def memory_page_markdown(self, memory_id: str, memory: dict[str, Any]) -> str:
        keywords = memory.get("strong_keywords") or memory.get("keywords", [])
        tags = [
            "memory-sync/memory",
            f"memory-sync/stage/{memory.get('stage', 'S1')}",
            f"agent/{self.memory_agent(memory)}",
        ]
        if memory_is_shared(memory):
            tags.append("memory-sync/shared")
        frontmatter = [
            "---",
            "type: memory",
            f"memory_id: {self.yaml_scalar(memory_id)}",
            f"stage: {self.yaml_scalar(memory.get('stage', 'S1'))}",
            f"source_agent: {self.yaml_scalar(self.memory_agent(memory))}",
            f"memory_lane: {self.yaml_scalar(memory.get('memory_lane') or ('official' if memory.get('stage') in {'S3', 'S4'} else 'pending'))}",
            f"source_file: {self.yaml_scalar(memory.get('source_file', ''))}",
            f"source_anchor: {self.yaml_scalar(memory.get('source_anchor', ''))}",
            f"expire_at: {self.yaml_scalar(memory.get('expire_at') or 'permanent')}",
            "keywords:",
            *self.yaml_list(keywords),
            "tags:",
            *self.yaml_list(tags),
            "---",
            "",
        ]
        lines = frontmatter + [
            f"# {memory.get('title', 'Untitled memory')}",
            "",
            str(memory.get("summary", "")).strip(),
            "",
            "## Status",
            "",
            f"- Stage: {memory.get('stage', 'S1')}",
            f"- Effective hits: {memory.get('effective_hit_count', 0)}",
            f"- Source agent: {self.memory_agent(memory)}",
            f"- Shared context: {'yes' if memory_is_shared(memory) else 'no'}",
            "",
            "## Links",
            "",
            f"- Index: [[{OBSIDIAN_INDEX_FILE}]]",
            f"- User profile: [[{PROFILE_MD_FILE}]]",
        ]
        source = str(memory.get("source_file", ""))
        if source:
            lines.append(f"- Source: [[{source}]]")
        if memory.get("permanent_file"):
            lines.append(f"- Permanent: [[{memory['permanent_file']}]]")
        if keywords:
            lines.extend(["", "## Keywords", "", ", ".join(str(item) for item in keywords[:12])])
        excerpt = str(memory.get("excerpt", "")).strip()
        if excerpt:
            lines.extend(["", "## Evidence", "", excerpt])
        return "\n".join(lines).rstrip() + "\n"

    def write_obsidian_memory_pages(self) -> None:
        page_dir = self.vault_path / MEMORY_PAGES_DIR
        expected: set[Path] = set()
        for memory_id, memory in self.store.memories().items():
            rel = self.memory_page_rel(memory_id, memory)
            path = self.vault_path / rel
            expected.add(path.resolve())
            self.write_text_atomic(path, self.memory_page_markdown(memory_id, memory))
        if page_dir.exists():
            for path in page_dir.glob("memory_*.md"):
                if path.resolve() not in expected:
                    path.unlink()

    def write_memory_dashboard(self, profile: dict[str, Any] | None = None, context: dict[str, Any] | None = None) -> None:
        memories = self.store.memories()
        counts = Counter(memory.get("stage", "S1") for memory in memories.values())
        shared_count = sum(1 for memory in memories.values() if memory_is_shared(memory))
        top_memories = self.memory_snapshot(limit=8, shared_only=True)
        profile_brief = ""
        if profile:
            profile_brief = str(profile.get("profile_brief", ""))
        elif context:
            profile_brief = str(context.get("profile_brief", ""))
        lines = [
            "# Memory Dashboard",
            "",
            "> 自动生成的 Obsidian 记忆入口。JSON 仍是机器真相源；这里用于浏览、反链、筛选和人工校验。",
            "",
            f"- Generated: {now_iso()}",
            f"- Total memories: {len(memories)}",
            f"- Shared memories: {shared_count}",
            f"- Stage distribution: S1={counts.get('S1', 0)}, S2={counts.get('S2', 0)}, S3={counts.get('S3', 0)}, S4={counts.get('S4', 0)}",
            "",
            "## Core Links",
            "",
            f"- [[{OBSIDIAN_INDEX_FILE}]]",
            f"- [[{PROFILE_MD_FILE}]]",
            f"- [[_shared/context/agent_brief.md]]",
            f"- [[_context/agent_brief.md]]",
            "",
        ]
        if profile_brief:
            lines.extend(["## User Brief", "", profile_brief, ""])
        lines.extend(["## Shared Memory Snapshot", ""])
        if not top_memories:
            lines.extend(["_No shared memories yet._", ""])
        for memory in top_memories:
            memory_id = str(memory.get("id", ""))
            page = self.memory_page_rel(memory_id, memories[memory_id]) if memory_id in memories else ""
            title = str(memory.get("title", "Untitled memory"))
            lines.append(f"- [[{page}|{memory_id}]] [{memory.get('stage')}] {title}")
            if memory.get("summary"):
                lines.append(f"  - {compact_text(str(memory.get('summary')), 140)}")
        lines.extend(["", "## Agent Stores", ""])
        for agent in ADAPTER_NAMES:
            lines.append(f"- {agent}: [[{AGENTS_DIR}/{agent}/index.json]]")
        lines.extend(["", "## Optional Dataview", "", "```dataview", f'TABLE stage, source_agent, expire_at FROM "{MEMORY_PAGES_DIR}" SORT stage DESC', "```", ""])
        self.write_text_atomic(self.vault_path / MEMORY_DASHBOARD_FILE, "\n".join(lines).rstrip() + "\n")

    def write_obsidian_surfaces(self, profile: dict[str, Any] | None = None, context: dict[str, Any] | None = None) -> None:
        self.write_obsidian_memory_pages()
        self.write_memory_dashboard(profile=profile, context=context)

    def memory_agent(self, memory: dict[str, Any]) -> str:
        return str(memory.get("source_agent") or "openclaw")

    def agent_dir(self, agent: str) -> Path:
        return self.vault_path / AGENTS_DIR / agent

    def agent_memories(self, agent: str) -> dict[str, dict[str, Any]]:
        return {
            memory_id: memory
            for memory_id, memory in self.store.memories().items()
            if self.memory_agent(memory) == agent
        }

    def write_json_atomic(self, path: Path, data: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)

    def write_text_atomic(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, path)

    def agent_memory_record(self, memory_id: str, memory: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": memory_id,
            "title": memory.get("title", ""),
            "summary": memory.get("summary", ""),
            "keywords": memory.get("keywords", []),
            "strong_keywords": memory.get("strong_keywords", []),
            "stage": memory.get("stage", "S1"),
            "memory_lane": memory.get("memory_lane") or ("official" if memory.get("stage") in {"S3", "S4"} else "pending"),
            "source_agent": self.memory_agent(memory),
            "source_confidence": memory.get("source_confidence") or ("distilled" if memory.get("candidate_origin") else "inferred"),
            "source_file": memory.get("source_file", ""),
            "source_anchor": memory.get("source_anchor", ""),
            "original_context_file": memory.get("original_context_file") or memory.get("source_file", ""),
            "original_context_anchor": memory.get("original_context_anchor") or memory.get("source_anchor", ""),
            "candidate_origin": memory.get("candidate_origin"),
            "candidate_uid": memory.get("candidate_uid"),
            "effective_hit_count": memory.get("effective_hit_count", 0),
            "expire_at": memory.get("expire_at"),
        }

    def write_agent_local_stores(self) -> None:
        for agent in ADAPTER_NAMES:
            base = self.agent_dir(agent)
            for name in ("daily", "summaries", "permanent"):
                (base / name).mkdir(parents=True, exist_ok=True)

            memories = self.agent_memories(agent)
            records = {
                memory_id: self.agent_memory_record(memory_id, memory)
                for memory_id, memory in sorted(memories.items())
            }
            payload = {
                "_meta": {
                    "schema": "memory-sync-agent-store",
                    "agent": agent,
                    "generated_at": now_iso(),
                    "record_count": len(records),
                },
                "memories": records,
            }
            self.write_json_atomic(base / "index.json", payload)

            by_date: dict[str, list[dict[str, Any]]] = {}
            for memory_id, memory in memories.items():
                source = str(memory.get("source_file", ""))
                match = re.search(r"(\d{4}-\d{2}-\d{2})\.md", source)
                day = match.group(1) if match else "undated"
                by_date.setdefault(day, []).append(self.agent_memory_record(memory_id, memory))
            summary_dir = base / "summaries"
            expected_summary_paths = {summary_dir / f"{day}.json" for day in by_date}
            for day, items in by_date.items():
                self.write_json_atomic(
                    base / "summaries" / f"{day}.json",
                    {
                        "_meta": {"schema": "memory-sync-agent-day-summary", "agent": agent, "date": day, "generated_at": now_iso()},
                        "items": items,
                    },
                )
            for old_summary in summary_dir.glob("*.json"):
                if old_summary not in expected_summary_paths:
                    old_summary.unlink()

        openclaw_daily = self.vault_path / VAULT_DAILY_DIR
        agent_daily = self.agent_dir("openclaw") / "daily"
        if openclaw_daily.exists():
            for path in openclaw_daily.glob("*.md"):
                target = agent_daily / path.name
                if not target.exists() or file_hash(path) != file_hash(target):
                    target.write_text(path.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")

    def shared_memory_records(self) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        for memory_id, memory in self.store.memories().items():
            if memory_is_shared(memory):
                result[memory_id] = self.agent_memory_record(memory_id, memory)
        return result

    def write_shared_layer(self, profile: dict[str, Any] | None = None, context: dict[str, Any] | None = None) -> None:
        shared_memories = self.shared_memory_records()
        self.write_json_atomic(
            self.vault_path / SHARED_MEMORY_INDEX,
            {
                "_meta": {
                    "schema": "memory-sync-shared-memory-index",
                    "generated_at": now_iso(),
                    "record_count": len(shared_memories),
                    "policy": "Only S3/S4, OpenClaw distilled, or effectively used memories enter the shared layer.",
                },
                "memories": shared_memories,
            },
        )
        if profile is not None:
            self.write_json_atomic(self.vault_path / SHARED_PROFILE_JSON, profile)
        if context is not None:
            self.write_json_atomic(self.vault_path / SHARED_CONTEXT_JSON, context)
            shared_context_dir = self.vault_path / SHARED_CONTEXT_DIR
            shared_context_dir.mkdir(parents=True, exist_ok=True)
            self.write_text_atomic(shared_context_dir / "agent_brief.md", self.adapter_markdown(context, "brief"))
            for adapter in ADAPTER_NAMES:
                self.write_text_atomic(shared_context_dir / f"{adapter}.md", self.adapter_markdown(context, adapter))

    def refresh_derived_outputs(self) -> None:
        self.write_agent_local_stores()
        profile = self.build_user_profile()
        self.save_user_profile(profile)
        context = self.build_agent_context(profile)
        if CONFIG["LEGACY_CONTEXT_ENABLED"]:
            self.write_agent_context("all", profile=profile, context=context)
        self.write_shared_layer(profile=profile, context=context)
        self.write_obsidian_surfaces(profile=profile, context=context)

    def git_run(self, args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", str(self.vault_path), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=check,
        )

    def run_in_dir(self, cwd: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args,
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def git_paths(self) -> list[str]:
        candidates = [
            f"_index/{INDEX_NAME}",
            f"_index/{PROFILE_NAME}",
            OBSIDIAN_INDEX_FILE,
            PROFILE_MD_FILE,
            MEMORY_DASHBOARD_FILE,
            MEMORY_PAGES_DIR,
            VAULT_DAILY_DIR,
            PERMANENT_DIR,
            AGENTS_DIR,
            SHARED_DIR,
        ]
        if CONFIG["LEGACY_CONTEXT_ENABLED"]:
            candidates.append(CONTEXT_DIR)
        return [path for path in candidates if (self.vault_path / path).exists()]

    def current_git_branch(self) -> str:
        configured = str(CONFIG["GIT_BRANCH"]).strip()
        if configured:
            return configured
        result = self.git_run(["branch", "--show-current"])
        return result.stdout.strip() or "main"

    def cmd_git_sync(self) -> int:
        probe = self.git_run(["rev-parse", "--is-inside-work-tree"])
        if probe.returncode != 0 or probe.stdout.strip() != "true":
            self.log(f"ERROR vault is not a git repository: {self.vault_path}")
            return 1

        paths = self.git_paths()
        if not paths:
            self.log("Git sync: no memory paths exist yet.")
            return 0

        add = self.git_run(["add", "--", *paths])
        if add.returncode != 0:
            self.log(add.stdout.strip())
            self.log(add.stderr.strip())
            return add.returncode
        staged = self.git_run(["diff", "--cached", "--quiet", "--", *paths])
        if staged.returncode == 0:
            self.log("Git sync: no staged memory changes.")
            return 0

        message = f"sync memory index {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        commit = self.git_run(["commit", "-m", message])
        if commit.returncode != 0:
            self.log(commit.stdout.strip())
            self.log(commit.stderr.strip())
            return commit.returncode

        self.log(commit.stdout.strip())
        if CONFIG["GIT_PUSH_ENABLED"]:
            push = self.git_run(["push", str(CONFIG["GIT_REMOTE"]), self.current_git_branch()])
            if push.returncode != 0:
                self.log(push.stdout.strip())
                self.log(push.stderr.strip())
                return push.returncode
            self.log(push.stdout.strip() or push.stderr.strip() or "Git push complete.")
        else:
            self.log("Git commit complete; push disabled by GIT_PUSH_ENABLED=false.")
        return 0

    def cmd_index_clean(self) -> int:
        removed: Counter[str] = Counter()
        kept = 0
        for memory_id, memory in list(self.store.memories().items()):
            reason = filter_reason(memory)
            if reason:
                removed[reason] += 1
                self.store.data.pop(memory_id, None)
                continue
            MemoryStore.refresh_keyword_profile(memory)
            kept += 1

        self.store.data[INDEX_META]["cleaned_at"] = now_iso()
        self.store.data[INDEX_META]["cleaned_removed"] = dict(removed)
        self.store.save()
        self.write_obsidian_index()
        self.log(f"Index clean complete: kept={kept}, removed={sum(removed.values())}")
        for reason, count in removed.most_common():
            self.log(f"  {reason}: {count}")
        return 0

    def cmd_status(self) -> int:
        memories = self.store.memories()
        counts = Counter(memory.get("stage", "S1") for memory in memories.values())
        self.log(f"Index: {self.store.index_path}")
        self.log(f"Memories: {len(memories)}")
        for stage in STAGES:
            self.log(f"  {stage}: {counts.get(stage, 0)}")
        processed = self.store.data.get(INDEX_META, {}).get("processed_files", {})
        self.log(f"Processed daily files: {len(processed)}")

        now = datetime.now()
        expiring: list[tuple[datetime, str, dict[str, Any]]] = []
        for memory_id, memory in memories.items():
            expire_at = parse_time(memory.get("expire_at"))
            if expire_at and expire_at > now and expire_at - now <= timedelta(days=3):
                expiring.append((expire_at, memory_id, memory))
        if expiring:
            self.log("Expiring within 3 days:")
            for expire_at, memory_id, memory in sorted(expiring)[:10]:
                self.log(f"- {memory_id} {memory.get('title')} at {expire_at.isoformat()}")
        return 0

    def profile_path(self) -> Path:
        return self.vault_path / "_index" / PROFILE_NAME

    def context_path(self, name: str) -> Path:
        return self.vault_path / CONTEXT_DIR / name

    def read_optional_text(self, path: Path, limit: int = 120000) -> str:
        if not path.exists() or not path.is_file():
            return ""
        return path.read_text(encoding="utf-8", errors="replace")[:limit]

    def collect_profile_sources(self) -> list[tuple[str, str, float]]:
        sources: list[tuple[str, str, float]] = []
        for rel, weight in [
            ("USER.md", 1.0),
            ("AGENTS.md", 0.9),
            ("MEMORY.md", 0.85),
            ("TOOLS.md", 0.55),
            ("SOUL.md", 0.4),
        ]:
            path = self.openclaw_path / rel
            text = self.read_optional_text(path)
            if text:
                sources.append((f"openclaw:{rel}", text, weight))

        codex_home = Path.home() / ".codex"
        for rel, weight in [
            ("AGENTS.md", 0.75),
            ("config.toml", 0.5),
            ("rules/default.rules", 0.55),
        ]:
            path = codex_home / rel
            text = self.read_optional_text(path)
            if text:
                sources.append((f"codex:{rel}", text, weight))

        skill_doc = ROOT / "SKILL.md"
        text = self.read_optional_text(skill_doc)
        if text:
            sources.append(("codex:memory-sync/SKILL.md", text, 0.45))
        return sources

    def add_rule_signals(self, profile: dict[str, Any], source: str, text: str, base_weight: float) -> None:
        lowered = text.lower()
        rules = [
            ("communication_style", "direct_concise", ["直接", "简洁", "concise", "direct", "少说话", "别太啰嗦", "啰嗦"], "Prefer direct, concise answers."),
            ("communication_style", "code_first", ["代码", "code", "code-first", "代码优先"], "Prefer concrete code and executable steps over long prose."),
            ("communication_style", "fast_response", ["快速", "快响应", "fast", "response time"], "Respond quickly and keep momentum."),
            ("decision_style", "plan_before_large_changes", ["先计划", "计划再", "plan", "strategy", "中长任务"], "Plan before multi-step or risky implementation."),
            ("decision_style", "iterate_while_building", ["边做边调整", "iterate", "实践 > 理论", "practice"], "Iterate through working artifacts rather than staying theoretical."),
            ("risk_preference", "confirm_before_deletion", ["删除", "delete", "destructive", "confirm before deleting", "always confirm"], "Confirm before deleting or destructive operations."),
            ("risk_preference", "do_not_exfiltrate", ["private", "隐私", "exfiltrate", "nothing goes external", "外部"], "Treat private data and external actions carefully."),
            ("workflows", "git_versioned_memory", ["git", "github", "版本", "version", "push", "commit"], "Use Git/GitHub for versioned memory assets."),
            ("workflows", "obsidian_memory_surface", ["obsidian", "vault", "知识库"], "Use Obsidian as the readable memory surface."),
            ("active_projects", "memory-sync", ["memory-sync", "openclaw memory", "agent context", "user_profile", "agent_context"], "Memory-sync is the current context portability project."),
            ("active_projects", "context_portability", ["context portability", "agent context", "context pack", "上下文迁移"], "Context portability across agents is an important recurring project."),
            ("tool_preferences", "powershell_python_js", ["powershell", "python", "javascript", "pytest"], "Comfortable with PowerShell, Python, JavaScript, and pytest workflows."),
            ("tool_preferences", "multi_agent_context", ["codex", "claude", "openclaw", "opencode", "hermes"], "Needs low-cost switching across multiple agents."),
            ("prompt_preferences", "action_oriented", ["多做事", "主动", "proactive", "解决", "执行"], "Prefer action-oriented agents that inspect, implement, and verify."),
            ("do_not_assume", "avoid_unverified_summaries", ["总结不准", "证据", "evidence", "不要擅自"], "Keep profile claims tied to evidence and avoid unsupported summaries."),
        ]
        for category, label, terms, detail in rules:
            matched = [term for term in terms if term.lower() in lowered]
            if not matched:
                continue
            profile["signals"].setdefault(category, []).append(
                signal(category, label, base_weight, source, f"matched: {', '.join(matched[:4])}", detail)
            )

    def add_memory_signals(self, profile: dict[str, Any]) -> None:
        stage_weight = {"S1": 0.35, "S2": 0.55, "S3": 0.75, "S4": 0.95}
        for memory_id, memory in self.store.memories().items():
            stage = str(memory.get("stage", "S1"))
            weight = stage_weight.get(stage, 0.35)
            weight += min(0.2, int(memory.get("effective_hit_count", 0)) * 0.05)
            source = f"memory-index:{memory_id}"
            text = "\n".join(
                [
                    str(memory.get("title", "")),
                    str(memory.get("summary", "")),
                    str(memory.get("excerpt", "")),
                    " ".join(str(item) for item in memory.get("strong_keywords", [])),
                ]
            )
            self.add_rule_signals(profile, source, text, weight)
            for keyword in memory.get("strong_keywords", [])[:8]:
                token = str(keyword).strip()
                if not token or is_generic_keyword(token) or is_low_signal_profile_label(token):
                    continue
                label = canonical_glossary_label(token)
                if is_low_signal_profile_label(label):
                    continue
                profile["signals"].setdefault("domain_glossary", []).append(
                    signal("domain_glossary", label, weight, source, text, "Strong keyword from memory index.")
                )
            title = memory_project_label(memory)
            if title:
                profile["signals"].setdefault("active_projects", []).append(
                    signal("active_projects", title[:80], weight, source, text, f"Stage {stage} memory.")
                )

    def summarize_profile_signals(self, profile: dict[str, Any]) -> None:
        summary: dict[str, list[dict[str, Any]]] = {}
        for category, items in profile.get("signals", {}).items():
            bucket: dict[str, dict[str, Any]] = {}
            for item in items:
                label = str(item.get("label", "")).strip()
                if not label:
                    continue
                if category == "domain_glossary":
                    label = canonical_glossary_label(label)
                if category in {"domain_glossary", "active_projects"} and is_low_signal_profile_label(label):
                    continue
                current = bucket.setdefault(
                    label,
                    {
                        "label": label,
                        "score": 0.0,
                        "confidence": 0.0,
                        "evidence": [],
                        "detail": item.get("detail", ""),
                    },
                )
                weight = float(item.get("weight", 0))
                current["score"] += weight
                current["confidence"] = max(float(current["confidence"]), float(item.get("confidence", 0)))
                if len(current["evidence"]) < 4:
                    current["evidence"].append({"source": item.get("source"), "evidence": item.get("evidence")})
            summary[category] = sorted(
                bucket.values(),
                key=lambda value: (float(value.get("score", 0)), float(value.get("confidence", 0))),
                reverse=True,
            )[:12]
        profile["summary"] = summary
        profile["profile_brief"] = self.profile_brief_text(profile)

    def profile_brief_text(self, profile: dict[str, Any]) -> str:
        summary = profile.get("summary", {})
        prefs = [item["label"] for item in summary.get("communication_style", [])[:3]]
        projects = [item["label"] for item in summary.get("active_projects", [])[:3]]
        tools = [item["label"] for item in summary.get("tool_preferences", [])[:3]]
        lines = []
        if prefs:
            lines.append("Communication: " + ", ".join(prefs))
        if projects:
            lines.append("Active focus: " + "; ".join(projects))
        if tools:
            lines.append("Tool context: " + ", ".join(tools))
        lines.append("Use evidence-backed memory; keep OpenClaw source read-only and version Obsidian outputs.")
        return " ".join(lines)

    def build_user_profile(self) -> dict[str, Any]:
        profile: dict[str, Any] = {
            "_meta": {
                "schema": "memory-sync-user-profile",
                "version": 1,
                "generated_at": now_iso(),
                "vault": str(self.vault_path),
                "openclaw_workspace": str(self.openclaw_path),
            },
            "signals": {},
            "summary": {},
            "profile_brief": "",
        }
        for source, text, weight in self.collect_profile_sources():
            profile["signals"].setdefault("source_inventory", []).append(
                signal("source_inventory", source, weight, source, f"{len(text)} chars", "Profile source loaded.")
            )
            self.add_rule_signals(profile, source, text, weight)
        self.add_memory_signals(profile)
        self.summarize_profile_signals(profile)
        return profile

    def write_profile_markdown(self, profile: dict[str, Any]) -> None:
        path = self.vault_path / PROFILE_MD_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# User 画像",
            "",
            "> Auto-generated from USER.md, memory index, OpenClaw distilled signals, and local agent configuration. Keep claims evidence-backed.",
            "",
            f"- Generated: {profile['_meta']['generated_at']}",
            f"- Brief: {profile.get('profile_brief', '')}",
            "",
        ]
        for category, items in profile.get("summary", {}).items():
            lines.extend([f"## {category}", ""])
            if not items:
                lines.extend(["_none_", ""])
                continue
            for item in items[:8]:
                lines.append(f"- **{item['label']}** score={item['score']:.2f} confidence={item['confidence']:.2f}")
                evidence = item.get("evidence", [])
                if evidence:
                    lines.append(f"  - evidence: {evidence[0].get('source')} - {evidence[0].get('evidence')}")
            lines.append("")
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        os.replace(tmp, path)

    def save_user_profile(self, profile: dict[str, Any]) -> None:
        path = self.profile_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)
        self.write_profile_markdown(profile)

    def load_or_build_profile(self) -> dict[str, Any]:
        path = self.profile_path()
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        profile = self.build_user_profile()
        self.save_user_profile(profile)
        return profile

    def cmd_profile_build(self) -> int:
        profile = self.build_user_profile()
        self.save_user_profile(profile)
        self.write_agent_local_stores()
        self.write_shared_layer(profile=profile)
        self.write_obsidian_surfaces(profile=profile)
        self.log(f"Profile written: {self.vault_rel(self.profile_path())}")
        self.log(f"Profile markdown: {PROFILE_MD_FILE}")
        self.log(profile.get("profile_brief", ""))
        return 0

    def cmd_profile_show(self) -> int:
        profile = self.load_or_build_profile()
        self.log(profile.get("profile_brief", ""))
        for category in ["communication_style", "decision_style", "workflows", "active_projects", "tool_preferences"]:
            items = profile.get("summary", {}).get(category, [])[:5]
            if not items:
                continue
            self.log(f"{category}:")
            for item in items:
                self.log(f"- {item['label']} score={item['score']:.2f}")
        return 0

    def memory_snapshot(self, limit: int = 8, shared_only: bool = True) -> list[dict[str, Any]]:
        stage_score = {"S4": 4, "S3": 3, "S2": 2, "S1": 1}
        rows = []
        for memory_id, memory in self.store.memories().items():
            if shared_only and not memory_is_shared(memory):
                continue
            rows.append(
                (
                    stage_score.get(str(memory.get("stage", "S1")), 1) + int(memory.get("effective_hit_count", 0)),
                    memory_id,
                    memory,
                )
            )
        rows.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "id": memory_id,
                "stage": memory.get("stage", "S1"),
                "title": memory_context_title(memory),
                "summary": memory.get("summary", ""),
                "keywords": memory.get("strong_keywords") or memory.get("keywords", [])[:6],
                "source": memory.get("source_file", ""),
                "source_anchor": memory.get("source_anchor", ""),
                "source_agent": self.memory_agent(memory),
                "original_context_file": memory.get("original_context_file") or memory.get("source_file", ""),
                "original_context_anchor": memory.get("original_context_anchor") or memory.get("source_anchor", ""),
                "candidate_origin": memory.get("candidate_origin"),
            }
            for _score, memory_id, memory in rows[:limit]
        ]

    def build_agent_context(self, profile: dict[str, Any]) -> dict[str, Any]:
        summary = profile.get("summary", {})
        return {
            "_meta": {
                "schema": "memory-sync-agent-context",
                "version": 1,
                "generated_at": now_iso(),
            },
            "profile_brief": profile.get("profile_brief", ""),
            "communication_style": summary.get("communication_style", [])[:6],
            "decision_style": summary.get("decision_style", [])[:6],
            "risk_preference": summary.get("risk_preference", [])[:6],
            "workflows": summary.get("workflows", [])[:8],
            "active_projects": summary.get("active_projects", [])[:8],
            "domain_glossary": summary.get("domain_glossary", [])[:16],
            "tool_preferences": summary.get("tool_preferences", [])[:8],
            "prompt_preferences": summary.get("prompt_preferences", [])[:8],
            "do_not_assume": summary.get("do_not_assume", [])[:8],
            "memory_snapshot": self.memory_snapshot(shared_only=True),
            "paths": {
                "memory_index": f"_index/{INDEX_NAME}",
                "user_profile": f"_index/{PROFILE_NAME}",
                "profile_markdown": PROFILE_MD_FILE,
                "daily_copies": VAULT_DAILY_DIR,
                "context_dir": SHARED_CONTEXT_DIR,
                "legacy_context_dir": CONTEXT_DIR if CONFIG["LEGACY_CONTEXT_ENABLED"] else None,
            },
        }

    def adapter_markdown(self, context: dict[str, Any], adapter: str) -> str:
        title = {
            "codex": "Codex Context",
            "claude": "Claude Context",
            "openclaw": "OpenClaw Context",
            "opencode": "OpenCode Context",
            "hermes-agent": "Hermes Agent Handoff",
            "brief": "Agent Brief",
        }.get(adapter, adapter)
        lines = [f"# {title}", "", f"Generated: {context['_meta']['generated_at']}", "", "## User Brief", "", context.get("profile_brief", ""), ""]
        if adapter == "hermes-agent":
            lines.extend([
                "## Handoff Protocol",
                "",
                "- Carry the user's stable preferences, active projects, and current memory snapshot between agents.",
                "- Preserve evidence references; do not invent profile facts.",
                "- Prefer concise task state, clear next actions, and source paths.",
                "- Treat external publishing, destructive cleanup, and GitHub push as explicit-action zones.",
                "",
            ])
        elif adapter == "codex":
            lines.extend(["## Codex Operating Notes", "", "- Inspect files first, implement surgically, verify with commands.", "- Keep OpenClaw source read-only; write Obsidian/Git outputs only.", ""])
        elif adapter == "claude":
            lines.extend(["## Claude Operating Notes", "", "- Use the structured profile as stable context, then reason through ambiguity before writing.", "- Keep responses concise and evidence-backed.", ""])
        elif adapter == "openclaw":
            lines.extend(["## OpenClaw Operating Notes", "", "- This is a distilled user/context state for continuity.", "- Raw memory remains in OpenClaw; Obsidian index is the persistent projection.", ""])
        elif adapter == "opencode":
            lines.extend(["## OpenCode Operating Notes", "", "- Optimize for direct implementation context and minimal prose.", "- Use paths and commands from the context package.", ""])

        for key, heading in [
            ("communication_style", "Communication"),
            ("decision_style", "Decision Style"),
            ("risk_preference", "Risk Boundaries"),
            ("workflows", "Workflows"),
            ("tool_preferences", "Tools"),
            ("active_projects", "Active Projects"),
            ("domain_glossary", "Glossary"),
            ("do_not_assume", "Do Not Assume"),
        ]:
            items = context.get(key, [])
            if not items:
                continue
            lines.extend([f"## {heading}", ""])
            for item in items[:8]:
                evidence = item.get("evidence", [])
                ref = f" ({evidence[0].get('source')})" if evidence else ""
                lines.append(f"- {item.get('label')} [score={float(item.get('score', 0)):.2f}]{ref}")
            lines.append("")

        memories = context.get("memory_snapshot", [])
        if memories:
            lines.extend(["## Memory Snapshot", ""])
            for memory in memories:
                lines.append(f"- {memory.get('id')} [{memory.get('stage')}] {memory.get('title')}")
                if memory.get("summary"):
                    lines.append(f"  Summary: {compact_text(str(memory.get('summary')), 160)}")
                source = memory.get("original_context_file") or memory.get("source")
                anchor = memory.get("original_context_anchor") or memory.get("source_anchor")
                if source:
                    lines.append(f"  Source: [[{source}]]{f' {anchor}' if anchor else ''}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    def write_agent_context(
        self,
        adapter: str = "all",
        profile: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[str]:
        if not CONFIG["LEGACY_CONTEXT_ENABLED"]:
            return []
        if profile is None:
            profile = self.load_or_build_profile()
        if context is None:
            context = self.build_agent_context(profile)
        base = self.vault_path / CONTEXT_DIR
        base.mkdir(parents=True, exist_ok=True)
        json_path = self.vault_path / CONTEXT_JSON
        json_path.write_text(json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8")

        written = [self.vault_rel(json_path)]
        adapters = ADAPTER_NAMES if adapter == "all" else (adapter,)
        brief_path = base / "agent_brief.md"
        brief_path.write_text(self.adapter_markdown(context, "brief"), encoding="utf-8")
        written.append(self.vault_rel(brief_path))
        for name in adapters:
            if name not in ADAPTER_NAMES:
                raise ValueError(f"Unknown adapter: {name}")
            path = base / f"{name}.md"
            path.write_text(self.adapter_markdown(context, name), encoding="utf-8")
            written.append(self.vault_rel(path))
        return written

    def cmd_context_export(self, adapter: str = "all") -> int:
        profile = self.load_or_build_profile()
        context = self.build_agent_context(profile)
        written = self.write_agent_context(adapter, profile=profile, context=context)
        self.write_agent_local_stores()
        self.write_shared_layer(profile=profile, context=context)
        self.write_obsidian_surfaces(profile=profile, context=context)
        if adapter == "all":
            shared_written = [f"{SHARED_CONTEXT_DIR}/agent_brief.md"] + [f"{SHARED_CONTEXT_DIR}/{name}.md" for name in ADAPTER_NAMES]
        else:
            shared_written = [f"{SHARED_CONTEXT_DIR}/agent_brief.md", f"{SHARED_CONTEXT_DIR}/{adapter}.md"]
        self.log("Shared context files written:")
        for item in shared_written:
            self.log(f"- {item}")
        if written:
            self.log("Legacy _context files written:")
        for item in written:
            self.log(f"- {item}")
        return 0

    def read_ingest_input(self, args: list[str]) -> str:
        if not args:
            if sys.stdin.isatty():
                raise ValueError("ingest requires text, --stdin, --file <path>, or --project <path>")
            return sys.stdin.read()
        if args[0] == "--stdin":
            if len(args) != 1:
                raise ValueError("ingest --stdin takes no extra arguments")
            return sys.stdin.read()
        if args[0] == "--file":
            if len(args) != 2:
                raise ValueError("ingest --file requires exactly one path")
            path = Path(args[1]).expanduser()
            if not path.exists() or not path.is_file():
                raise ValueError(f"ingest file not found: {path}")
            return path.read_text(encoding="utf-8", errors="replace")
        if args[0] == "--project":
            if len(args) < 2:
                raise ValueError("ingest --project requires a path")
            path = expand_path(args[1])
            note = ""
            if len(args) > 2:
                if args[2] != "--note":
                    raise ValueError("ingest --project accepts only optional --note text")
                note = " ".join(args[3:])
            return self.project_handoff_text(path, note)
        return " ".join(args)

    def project_handoff_text(self, project_path: Path, note: str = "") -> str:
        if not project_path.exists() or not project_path.is_dir():
            raise ValueError(f"project path not found: {project_path}")
        interesting = [
            "SKILL.md",
            "README.md",
            ".env.example",
            "scripts/main.py",
            "config/filters.json",
            "config/keywords.json",
            "config/triggers.json",
        ]
        summaries = []
        for rel in interesting:
            path = project_path / rel
            if path.exists() and path.is_file():
                item = file_summary(path)
                summaries.append(
                    f"- {rel}: size={item['size']} lines={item['lines']} sha256={item['sha256']}"
                )
        command_probe = self.run_in_dir(project_path, [sys.executable, "scripts/main.py", "help"])
        commands = [
            line.strip()
            for line in command_probe.stdout.splitlines()
            if line.strip().startswith("python scripts/main.py")
        ]
        git_probe = self.run_in_dir(project_path, ["git", "status", "--short"])
        git_status = git_probe.stdout.strip() if git_probe.returncode == 0 else "not a git repository"
        lines = [
            f"project: {project_path.name}",
            f"path: {project_path}",
            f"captured_at: {now_iso()}",
            "decision: capture actual project state for multi-agent handoff instead of only chat summary.",
            "source: local project files, command surface, and git status.",
        ]
        if note:
            lines.append(f"note: {note}")
        lines.extend(["", "files:", *summaries])
        if commands:
            lines.extend(["", "commands:", *[f"- {command}" for command in commands]])
        lines.extend(["", "git_status:", git_status or "clean"])
        return "\n".join(lines).rstrip() + "\n"

    def cmd_ingest(self, agent: str, text: str) -> int:
        if agent not in ADAPTER_NAMES:
            self.log(f"ERROR unknown agent: {agent}")
            return 1
        text = text.strip()
        if not text:
            self.log("ERROR ingest text is empty")
            return 1

        now = datetime.now()
        day = now.date().isoformat()
        base = self.agent_dir(agent)
        daily_dir = base / "daily"
        daily_dir.mkdir(parents=True, exist_ok=True)
        daily_path = daily_dir / f"{day}.md"
        summary = extract_summary(text, limit=360)
        header = f"## {now.replace(microsecond=0).isoformat()} {agent} ingest"
        prefix = "\n".join([header, "", "### Summary", "", summary, "", "### Original Context", ""])
        block = prefix + text.rstrip() + "\n\n"
        if daily_path.exists():
            old = daily_path.read_text(encoding="utf-8", errors="replace")
            daily_path.write_text(old.rstrip() + "\n\n" + block, encoding="utf-8")
            start_line = len(old.splitlines()) + 2
        else:
            daily_path.write_text(f"# {agent} daily {day}\n\n" + block, encoding="utf-8")
            start_line = 3

        rel = self.vault_rel(daily_path)
        original_start_line = start_line + len(prefix.splitlines())
        anchor = f"line {original_start_line}-{start_line + len(block.splitlines()) - 1}"
        title = title_from_ingest(text, agent)
        indexed_body = ingest_index_body(summary, rel, anchor)
        candidate = self.build_agent_ingest_memory(agent, title, indexed_body, rel, anchor)
        candidate["summary"] = summary
        candidate["excerpt"] = indexed_body
        reason = noise_reason_for_text(text)
        if reason:
            self.log(f"Stored agent daily only; not indexed reason={reason}: {rel}")
        else:
            memory_id = self.add_or_merge(candidate)
            self.store.save()
            self.log(f"Ingest indexed: {memory_id} [{candidate.get('stage')}] {title}")

        self.refresh_derived_outputs()
        self.log(f"Agent ingest stored: {rel}")
        return 0

    def cmd_candidates(self, agent: str | None = None) -> int:
        rows = []
        for memory_id, memory in self.store.memories().items():
            if agent and self.memory_agent(memory) != agent:
                continue
            if memory.get("candidate_origin") or memory.get("source_type") in {"agent_ingest", "openclaw_distilled"}:
                rows.append((memory_id, memory))
        rows.sort(key=lambda item: (str(item[1].get("source_agent", "")), str(item[1].get("stage", "")), item[0]))
        self.log(f"Candidate memories: {len(rows)}")
        for memory_id, memory in rows:
            self.log(
                f"- {memory_id} [{memory.get('stage')}] agent={self.memory_agent(memory)} "
                f"origin={memory.get('candidate_origin')} {memory.get('title')}"
            )
        return 0

    def cmd_handoff(self, agent: str) -> int:
        if agent not in ADAPTER_NAMES:
            self.log(f"ERROR unknown agent: {agent}")
            return 1
        profile = self.load_or_build_profile()
        context = self.build_agent_context(profile)
        if CONFIG["LEGACY_CONTEXT_ENABLED"]:
            self.write_agent_context(agent, profile=profile, context=context)
        self.write_shared_layer(profile=profile, context=context)
        self.write_obsidian_surfaces(profile=profile, context=context)
        text = self.adapter_markdown(context, agent)
        self.log(text)
        return 0

    def cmd_context_brief(self) -> int:
        profile = self.load_or_build_profile()
        context = self.build_agent_context(profile)
        text = self.adapter_markdown(context, "brief")
        self.write_shared_layer(profile=profile, context=context)
        if CONFIG["LEGACY_CONTEXT_ENABLED"]:
            path = self.vault_path / CONTEXT_DIR / "agent_brief.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        self.log(text)
        return 0

    def cmd_context_doctor(self) -> int:
        profile = self.load_or_build_profile()
        context = self.build_agent_context(profile)
        issues = []
        if not self.profile_path().exists():
            issues.append("missing user_profile.json")
        if CONFIG["LEGACY_CONTEXT_ENABLED"] and not (self.vault_path / CONTEXT_DIR).exists():
            issues.append("missing legacy _context directory")
        if not (self.vault_path / MEMORY_DASHBOARD_FILE).exists():
            issues.append("missing Obsidian memory dashboard")
        if not (self.vault_path / MEMORY_PAGES_DIR).exists():
            issues.append("missing Obsidian memory pages directory")
        if not (self.vault_path / AGENTS_DIR).exists():
            issues.append("missing _agents directory")
        if not (self.vault_path / SHARED_DIR).exists():
            issues.append("missing _shared directory")
        if not (self.vault_path / SHARED_CONTEXT_DIR).exists():
            issues.append("missing _shared/context directory")
        if len(profile.get("summary", {}).get("communication_style", [])) == 0:
            issues.append("communication_style has no signals")
        if len(profile.get("summary", {}).get("active_projects", [])) == 0:
            issues.append("active_projects has no signals")
        stale_at = parse_time(profile.get("_meta", {}).get("generated_at"))
        if stale_at and datetime.now() - stale_at > timedelta(days=7):
            issues.append("profile older than 7 days")
        noisy_glossary = [
            str(item.get("label"))
            for item in profile.get("summary", {}).get("domain_glossary", [])
            if is_low_signal_profile_label(str(item.get("label", "")))
        ]
        if noisy_glossary:
            issues.append("domain_glossary still has low-signal labels: " + ", ".join(noisy_glossary[:5]))
        s1_snapshot = [item.get("id") for item in context.get("memory_snapshot", []) if item.get("stage") == "S1"]
        if s1_snapshot:
            issues.append("shared context snapshot contains S1 memories: " + ", ".join(str(item) for item in s1_snapshot[:5]))
        if issues:
            self.log("Context doctor issues:")
            for issue in issues:
                self.log(f"- {issue}")
        else:
            self.log("Context doctor: OK")
        return 0

    def cmd_autopilot(self) -> int:
        self.log("Autopilot start")
        result = self.cmd_sync()
        if result != 0:
            return result
        status = self.cmd_status()
        if status != 0:
            return status
        if CONFIG["GIT_SYNC_ENABLED"]:
            return self.cmd_git_sync()
        self.log("Git sync skipped; set GIT_SYNC_ENABLED=true to include it in autopilot.")
        return 0


def usage() -> None:
    print("Memory Sync")
    print("")
    print("Usage:")
    print("  python scripts/main.py sync")
    print("  python scripts/main.py search <keyword>")
    print("  python scripts/main.py diagnose <text>")
    print("  python scripts/main.py ingest <agent> [--stdin|--file path|--project path|text]")
    print("  python scripts/main.py handoff <agent>")
    print("  python scripts/main.py candidates [agent]")
    print("  python scripts/main.py trigger check <text>")
    print("  python scripts/main.py trigger hit <text>")
    print("  python scripts/main.py index clean")
    print("  python scripts/main.py profile build")
    print("  python scripts/main.py profile show")
    print("  python scripts/main.py context export [all|codex|claude|openclaw|opencode|hermes-agent]")
    print("  python scripts/main.py context brief")
    print("  python scripts/main.py context doctor")
    print("  python scripts/main.py git sync")
    print("  python scripts/main.py status")
    print("  python scripts/main.py autopilot")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if not args or args[0] in {"help", "-h", "--help"}:
        usage()
        return 0

    command = args[0]
    try:
        app = MemorySync()
    except ValueError as exc:
        print(f"ERROR {exc}")
        return 1

    if command == "sync":
        if len(args) != 1:
            print("ERROR sync takes no extra arguments")
            return 1
        return app.cmd_sync()
    if command == "search":
        if len(args) < 2:
            print("ERROR search requires a keyword")
            return 1
        return app.cmd_search(" ".join(args[1:]))
    if command == "diagnose":
        if len(args) < 2:
            print("ERROR diagnose requires text")
            return 1
        return app.cmd_diagnose(" ".join(args[1:]))
    if command == "ingest":
        if len(args) < 2:
            print("ERROR ingest requires: <agent> [--stdin|--file path|text]")
            return 1
        agent = args[1]
        if agent not in ADAPTER_NAMES:
            print(f"ERROR unknown agent: {agent}")
            return 1
        try:
            text = app.read_ingest_input(args[2:])
        except ValueError as exc:
            print(f"ERROR {exc}")
            return 1
        return app.cmd_ingest(agent, text)
    if command == "handoff":
        if len(args) != 2:
            print("ERROR handoff requires: <agent>")
            return 1
        return app.cmd_handoff(args[1])
    if command == "candidates":
        if len(args) > 2:
            print("ERROR candidates accepts at most one agent")
            return 1
        agent = args[1] if len(args) == 2 else None
        if agent is not None and agent not in ADAPTER_NAMES:
            print(f"ERROR unknown agent: {agent}")
            return 1
        return app.cmd_candidates(agent)
    if command == "trigger":
        if len(args) < 3 or args[1] not in {"check", "hit"}:
            print("ERROR trigger requires: check <text> or hit <text>")
            return 1
        text = " ".join(args[2:])
        if args[1] == "check":
            return app.cmd_trigger_check(text)
        return app.cmd_trigger_hit(text)
    if command == "git":
        if len(args) != 2 or args[1] != "sync":
            print("ERROR git requires: sync")
            return 1
        return app.cmd_git_sync()
    if command == "index":
        if len(args) != 2 or args[1] != "clean":
            print("ERROR index requires: clean")
            return 1
        return app.cmd_index_clean()
    if command == "profile":
        if len(args) != 2 or args[1] not in {"build", "show"}:
            print("ERROR profile requires: build or show")
            return 1
        if args[1] == "build":
            return app.cmd_profile_build()
        return app.cmd_profile_show()
    if command == "context":
        if len(args) < 2 or args[1] not in {"export", "brief", "doctor"}:
            print("ERROR context requires: export [adapter], brief, or doctor")
            return 1
        if args[1] == "export":
            adapter = args[2] if len(args) == 3 else "all"
            if adapter != "all" and adapter not in ADAPTER_NAMES:
                print(f"ERROR unknown adapter: {adapter}")
                return 1
            return app.cmd_context_export(adapter)
        if len(args) != 2:
            print(f"ERROR context {args[1]} takes no extra arguments")
            return 1
        if args[1] == "brief":
            return app.cmd_context_brief()
        return app.cmd_context_doctor()
    if command == "status":
        if len(args) != 1:
            print("ERROR status takes no extra arguments")
            return 1
        return app.cmd_status()
    if command == "autopilot":
        if len(args) != 1:
            print("ERROR autopilot takes no extra arguments")
            return 1
        return app.cmd_autopilot()

    print(f"ERROR unknown command: {command}")
    usage()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
