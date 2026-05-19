---
name: memory-sync
description: Synchronize OpenClaw memory and multi-agent handoffs into Obsidian as a fast retention and context portability layer. Copies OpenClaw daily files, imports recall/dreaming/MEMORY candidates, preserves non-daily agent knowledge into Personal/Agent Knowledge, syncs installed skill inventories, ingests Codex/Claude/OpenClaw/OpenCode/hermes-agent handoff summaries, keeps per-agent stores under _agents, builds shared assets under _shared, maintains JSON/Markdown indexes, builds user profile, exports context packs, applies S1-S4 TTL, supports trigger check/hit, safe Obsidian-only cleanup, and optional Git/GitHub sync. Use for memory sync, ingest codex, candidates, handoff openclaw, skills sync, search, profile build, context export, hermes-agent handoff, git sync, status, or autopilot.
---

# Memory Sync

Use this skill as an OpenClaw companion and multi-agent handoff layer, not a replacement for OpenClaw's own recall/promotion system. OpenClaw remains the raw memory and slow distillation engine. This skill is the fast Obsidian/Git retention and context portability layer: copy first, index quickly, ingest agent handoff summaries, strengthen by use, forget safely, import OpenClaw's distilled candidates, keep each agent's local store separate, then publish shared profile/context/permanent knowledge for portability.

## Core Model

- Treat `OPENCLAW_WORKSPACE` as read-only.
- Copy `memory/YYYY-MM-DD.md` into `02-Lessons/OpenClaw-Daily/` before indexing.
- Search only `_index/openclaw_memory_index.json`.
- Generate `03-Reference/OpenClaw记忆索引.md` as the human-readable Obsidian entry.
- Generate `03-Reference/Memory Dashboard.md` and `03-Reference/Memories/` cards so Obsidian is a readable memory console, not only a file sink.
- Import OpenClaw distilled signals from `.dreams/short-term-recall.json`, `.dreams/phase-signals.json`, `memory/dreaming/rem/`, `memory/dreaming/deep/`, and promoted `MEMORY.md` entries.
- Preserve non-daily agent knowledge such as `MEMORY.md`, `USER.md`, `AGENTS.md`, and tool/config notes into `Personal/Agent Knowledge/<agent>/`.
- Detect high-value process memories such as success patterns, corrections, failure lessons, and user rules; these enter as S2 `process_memory` records.
- Ingest explicit handoff summaries from Codex, Claude, OpenClaw, OpenCode, and hermes-agent into their own `_agents/<agent>/daily/` lane before indexing.
- Build `_index/user_profile.json` and `03-Reference/User画像.md` from USER.md, the memory index, and local agent configuration.
- Export portable adapter context under `_shared/context/` for Codex, Claude, OpenClaw, OpenCode, and hermes-agent.
- Export installed skill inventory under `_shared/agent_skills.json`, `_agents/<agent>/skills.json`, and `Personal/Agent Knowledge/Agent Skills.md`.
- Treat `_context/` as a legacy compatibility output only; it is disabled by default unless `LEGACY_CONTEXT_ENABLED=true`.
- Keep per-agent local stores under `_agents/<agent>/` with separate `daily/`, `summaries/`, `index.json`, and `permanent/`.
- Keep portable shared distilled assets under `_shared/`, including shared memory, profile, context JSON, and adapter Markdown.
- Reject direct legacy/session sources such as `.dreams/session-corpus` and `main/sessions/*.jsonl` unless OpenClaw has distilled them back to a valid daily-file evidence path.
- Remove only Obsidian daily copies, and only when no indexed memory references them.
- Commit/push only through explicit `git sync` or `GIT_SYNC_ENABLED=true` autopilot.

## Workflow

Run commands from the skill folder:

```bash
python scripts/main.py sync
python scripts/main.py review prepare
python scripts/main.py review apply decisions.json
python scripts/main.py ingest codex --project D:/memory-sync-skill --note "current project handoff"
python scripts/main.py ingest codex --stdin
python scripts/main.py ingest claude --file session.md
python scripts/main.py ingest opencode "decision: ..."
python scripts/main.py candidates
python scripts/main.py handoff openclaw
python scripts/main.py search "keyword"
python scripts/main.py diagnose "text"
python scripts/main.py trigger check "text"
python scripts/main.py trigger hit "text"
python scripts/main.py index clean
python scripts/main.py profile build
python scripts/main.py profile show
python scripts/main.py context export all
python scripts/main.py context export hermes-agent
python scripts/main.py context brief
python scripts/main.py context doctor
python scripts/main.py skills sync
python scripts/main.py git sync
python scripts/main.py status
python scripts/main.py autopilot
```

## Agent Review Mode

Default mode is `MEMORY_SYNC_REVIEW_MODE=agent`. In this mode the script does not call an external LLM API and does not silently use rule-only indexing. The current agent running this skill is the reviewer.

When the user asks to run memory sync in agent mode:

```text
1. Run `python scripts/main.py review prepare`.
2. Read the generated `_review/memory-sync/latest-pack.json`.
3. Review every candidate in that pack.
4. Write a decisions JSON file with one decision per candidate.
5. Run `python scripts/main.py review apply <decisions.json>`.
6. Run `python scripts/main.py status` and, if requested or configured, `python scripts/main.py git sync`.
```

The script handles deterministic work: copying OpenClaw daily files into Obsidian, splitting source material, filtering obvious junk, preserving source anchors, validating decisions, writing JSON/Markdown surfaces, and keeping OpenClaw source files read-only.

The current agent handles judgment work: candidate selection, summary, keywords, S1-S4 rating, process-memory classification, and duplicate/merge suggestions.

Decision output must follow this shape:

```json
{
  "decisions": [
    {
      "candidate_id": "copy from latest-pack.json",
      "keep": true,
      "title": "short stable title",
      "summary": "evidence-backed summary",
      "keywords": ["specific", "searchable", "terms"],
      "strong_keywords": ["precise", "match", "terms"],
      "stage": "S2",
      "quality_score": 0.86,
      "memory_type": "process_memory",
      "lesson_type": "correction",
      "merge_with": null,
      "reason": "why this should be kept, discarded, or merged"
    }
  ]
}
```

Every candidate in the pack must have a decision. Use `"keep": false` for discarded material. Do not invent facts outside the candidate text. Preserve `source_file` and `source_anchor` by letting the script apply decisions rather than editing the index manually.

Use `MEMORY_SYNC_REVIEW_MODE=rules` only when the user explicitly wants the deterministic fallback, wants to save agent tokens, or needs a headless/offline run.

In `rules` mode, `sync` runs:

```text
copy OpenClaw daily files to Obsidian
-> create fast S1 memories from useful daily segments
-> import OpenClaw distilled candidates
-> ingest explicit agent handoffs when requested
-> merge duplicates
-> apply TTL/downgrade/cleanup rules
-> write JSON and Markdown indexes
-> build agent-local stores
-> build shared profile/context assets
-> preserve non-daily personal knowledge
-> sync installed skill inventory
-> build Obsidian dashboard and per-memory pages
```

Both modes refresh user profile and context outputs by default when `DERIVED_OUTPUTS_ENABLED=true`. Generated profile/context/shared files are rebuilt from current evidence, not appended incrementally.

## OpenClaw Distilled Import

Prefer OpenClaw's screened candidates over summarizing chat/session content directly.

Import priority:

```text
MEMORY.md promoted entries -> S4
dreaming/deep candidates -> S3
dreaming/rem possible lasting truths -> S3
short-term-recall high-score or recalled candidates -> S2/S3
plain daily segments -> S1
```

Imported records may include:

```text
candidate_origin
candidate_uid
openclaw_key
openclaw_score
openclaw_confidence
openclaw_recall_count
openclaw_daily_count
openclaw_grounded_count
openclaw_light_hits
openclaw_rem_hits
openclaw_concept_tags
```

Only import a distilled candidate when its evidence resolves to an existing `memory/YYYY-MM-DD.md` source that can be copied into Obsidian.

## Agent Handoff Ingest

Use `ingest <agent>` when the current agent needs to hand its session state to the shared memory layer:

```bash
python scripts/main.py ingest codex --stdin
python scripts/main.py ingest claude --file session.md
python scripts/main.py ingest hermes-agent "decision: keep OpenClaw source read-only; next action: run sync"
```

Supported agents are `codex`, `claude`, `openclaw`, `opencode`, and `hermes-agent`.

Ingest writes the submitted summary or captured project state to `_agents/<agent>/daily/YYYY-MM-DD.md` under `Summary` and `Original Context` sections. The index and portable context keep a compact summary plus `source_file`/`source_anchor` back to that original record. It creates an S1/S2 `agent_ingest` candidate when the content passes filters, merges duplicates into `_index/openclaw_memory_index.json`, then refreshes profile and `_shared` context outputs. It does not try to scrape hidden chat transcripts; the agent must submit a concise handoff summary or use `--project` to capture real project state.

When the user asks to sync the current chat, the active agent must write an explicit handoff summary and pipe it to `ingest <agent> --stdin`. The script cannot read hidden chat history by itself. A useful handoff should include: decisions, corrected assumptions, failed attempts, successful commands or steps, files changed, user preferences or constraints, open questions, and source links back to generated files where possible.

On Windows, prefer `--file handoff.md` for Chinese or mixed-language handoffs unless the shell is explicitly configured for UTF-8. Some PowerShell pipelines can replace non-ASCII stdin with `?` before Python receives it.

Use:

```bash
python scripts/main.py candidates
python scripts/main.py candidates codex
python scripts/main.py handoff openclaw
```

`handoff <agent>` prints and refreshes the adapter context for the target agent so OpenClaw can consume Codex/Claude/OpenCode work through `_shared/context/openclaw.md` or the printed handoff.

## Context Source Of Truth

Portable context source:

```text
_agents/<agent>/daily/        raw agent-submitted handoffs and project captures
_index/openclaw_memory_index.json
_index/user_profile.json
_shared/shared_memory_index.json
_shared/agent_context.json
_shared/context/<agent>.md
```

`_shared` is the portable context layer. `_context` is retained only for old integrations and is not generated unless `LEGACY_CONTEXT_ENABLED=true`.

## Retention

- `S1`: fast preserved memory, capacity-aware TTL of 3-10 days.
- `S2`: used once or backed by a strong OpenClaw recall signal, TTL of 7-15 days.
- `S3`: used repeatedly or surfaced by OpenClaw REM/deep signals, TTL of 14-30 days.
- `S4`: permanent memory, either hit-promoted or imported from OpenClaw `MEMORY.md` promotion.

Keep the "preserve first, forget later" principle: Obsidian copies and index entries can expire; OpenClaw source files must not be modified.

High-value process memories start at S2. This includes successful procedures, user corrections, failure lessons, and explicit operating rules. These memories are treated as behavior calibration data, not ordinary chatter.

## Personal Knowledge And Skill Inventory

Every sync refreshes personal knowledge outputs:

```text
Personal/Agent Knowledge/openclaw/MEMORY.md
Personal/Agent Knowledge/openclaw/USER.md
Personal/Agent Knowledge/openclaw/AGENTS.md
Personal/Agent Knowledge/openclaw/TOOLS.md
Personal/Agent Knowledge/codex/AGENTS.md
Personal/Agent Knowledge/codex/config.toml
Personal/Agent Knowledge/claude/CLAUDE.md
Personal/Agent Knowledge/opencode/AGENTS.md
Personal/Agent Knowledge/hermes-agent/AGENTS.md
Personal/Agent Knowledge/Agent Skills.md
Personal/Agent Knowledge/<agent>/Agent Skills.md
```

Skill inventory outputs:

```text
_shared/agent_skills.json
_agents/<agent>/skills.json
_agents/<agent>/skills.md
03-Reference/Agent Skills.md
Personal/Agent Knowledge/Agent Skills.md
Personal/Agent Knowledge/<agent>/Agent Skills.md
```

`03-Reference/Agent Skills.md` is the Obsidian navigation entry. `Personal/Agent Knowledge/Agent Skills.md` is the personal navigation entry. The detailed human-readable inventory is split by agent under `Personal/Agent Knowledge/<agent>/Agent Skills.md`, while `_agents/<agent>/skills.json` remains the machine-readable per-agent store.

The skill inventory records skill name, function summary, agent, level/source directory, local path, modified time, hash, enabled state, and frontmatter validity. OpenClaw is scanned across official npm, workspace, and user skill directories so multi-level installations are not missed. Markdown output language is inferred from the user's local profile/rules, or can be forced with `MEMORY_SYNC_LANGUAGE=zh` or `MEMORY_SYNC_LANGUAGE=en`.

## Trigger Logic

- Trigger words do not make the skill auto-run by themselves. `trigger check` and `trigger hit` are diagnostic/reinforcement commands after an agent or user has already decided to query memory-sync.
- `trigger check` is read-only.
- `trigger hit` is the only command that updates hit counters.
- Enforce one effective hit per memory per 24 hours.
- Treat trigger words as activation signals only.
- Require strong keyword evidence for a match.
- Detect noisy single-trigger reinforcement and downgrade or remove weak memories.

To make an agent automatically query this memory layer when the user mentions memory-related words, install an agent rule in that agent's own persistent rule file. Do not assume every agent uses OpenClaw's rule structure.

Recommended rule entry points:

| Agent | Rule entry point |
| --- | --- |
| OpenClaw | Workspace `AGENTS.md`, or the skill/workspace rule file that OpenClaw loads for the session |
| Codex | Project `AGENTS.md`, or user-level `~/.codex/AGENTS.md` |
| Claude Code | Project `CLAUDE.md`, project `.claude/CLAUDE.md`, or user-level `~/.claude/CLAUDE.md` |
| OpenCode | Project `AGENTS.md`, user-level `~/.config/opencode/AGENTS.md`, or `CLAUDE.md` when using Claude-compatible instructions |
| hermes-agent | Its configured system prompt/rule file; if there is no persistent rule file, provide `_shared/context/hermes-agent.md` as the handoff contract |

OpenClaw example:

````markdown
### 记忆触发词自动检索

当用户消息中包含以下触发词时，除了内置 `memory_search` 外，必须同时执行 memory-sync 的 search 命令。

触发词：记得、记忆、回忆、上次、之前、以前、曾经、历史、背景、上下文、仔细想想、想起来、记录、复盘、经验、remember、memory、recall、previous、last time、context

执行命令：

```bash
python /path/to/memory-sync/scripts/main.py search "关键词"
```

流程：

1. 内置 `memory_search` 搜 OpenClaw 工作区。
2. memory-sync `search` 搜 Obsidian 索引。
3. 合并两个结果再回答。
````

Generic non-OpenClaw rule template:

````markdown
### Memory-Sync Automatic Retrieval

When the user asks about memory, previous context, background, history, lessons, or prior decisions, query memory-sync before answering.

Trigger words: 记得、记忆、回忆、上次、之前、以前、曾经、历史、背景、上下文、仔细想想、想起来、记录、复盘、经验、remember、memory、recall、previous、last time、context

Command:

```bash
python /path/to/memory-sync/scripts/main.py search "keyword phrase"
```

Process:

1. Use the agent's built-in memory/context search if it has one.
2. Run memory-sync `search` against the Obsidian index.
3. Merge the results, cite uncertainty, and answer from the combined evidence.
````

Use the user's actual keyword phrase as the query, not the whole chat transcript. If the memory-sync command fails, tell the user the failure and continue with the agent's built-in memory/context results when available.

## Configuration

User-adjustable rules live in:

```text
config/filters.json
config/keywords.json
config/triggers.json
```

Execution mode is controlled by:

```text
MEMORY_SYNC_REVIEW_MODE=agent  # default
MEMORY_SYNC_REVIEW_MODE=rules  # deterministic fallback
```

- `MEMORY_SYNC_PROJECT_ROOTS`: optional path-list of project roots to scan for project-level `AGENTS.md`, `CLAUDE.md`, and `.claude/CLAUDE.md`.
- `MEMORY_SYNC_AGENT_KNOWLEDGE_FILES`: optional path-list of extra rule/profile files to copy into `Personal/Agent Knowledge/custom/` and use as profile evidence.
- `filters.json`: minimum segment length, source blacklist, text blacklist, and OpenClaw import thresholds.
- `keywords.json`: generic words, broad context words, domain phrases, blocked keyword patterns, and `strong_keyword_allowlist`.
- `triggers.json`: words that activate memory checks.

Keyword extraction should favor project names, code terms, and configured domain phrases. Profile/context generation filters low-signal labels such as pronouns, generic file names, broad tech words, and trigger words so they do not become glossary or active-project claims.

Use `diagnose` before changing rules:

```bash
python scripts/main.py diagnose "remember project retry policy API timeout WebSocket"
```

## User Profile And Agent Context

Use:

```bash
python scripts/main.py profile build
python scripts/main.py context export all
```

Profile outputs:

```text
_index/user_profile.json
03-Reference/User画像.md
```

Portable context outputs:

```text
_shared/agent_context.json
_shared/context/agent_brief.md
_shared/context/codex.md
_shared/context/claude.md
_shared/context/openclaw.md
_shared/context/opencode.md
_shared/context/hermes-agent.md
```

Each adapter context includes a memory retrieval contract that points to that agent's own rule entry point. OpenClaw uses `AGENTS.md`; Codex uses `AGENTS.md`; Claude Code uses `CLAUDE.md`; OpenCode uses `AGENTS.md` or Claude-compatible rules; hermes-agent uses its configured rule/system prompt or `_shared/context/hermes-agent.md` as a handoff contract. OpenClaw and hermes-agent also include stricter operating contracts for rule reading, conflict reporting, and source-memory safety.

Agent-local outputs:

```text
_agents/openclaw/daily/
_agents/openclaw/summaries/
_agents/openclaw/index.json
_agents/codex/index.json
_agents/claude/index.json
_agents/opencode/index.json
_agents/hermes-agent/index.json
```

Shared portable outputs:

```text
_shared/shared_memory_index.json
_shared/user_profile.json
_shared/agent_context.json
_shared/context/*.md
```

Obsidian-readable outputs:

```text
03-Reference/Memory Dashboard.md
03-Reference/Memories/memory_001.md
03-Reference/Memories/memory_002.md
```

Memory page file names are stable and ID-only (`memory_001.md`) so Obsidian, Git, and cross-platform sync do not break on long titles, punctuation, emoji, or renamed summaries. Each memory page includes YAML frontmatter, tags, source-agent metadata, wikilinks to the source daily copy, and links back to the index/profile. Shared context uses a stricter snapshot than the full index: S1 memories remain searchable in Obsidian but do not enter adapter context until OpenClaw distills them, the user reinforces them, or they reach a stronger stage.

The profile is evidence-backed. USER.md and explicit agent configuration get higher weight; S3/S4 and hit-promoted memories get strong weight; S1/S2 provide weaker recent context. Do not treat profile claims as truth unless they have evidence references.

Use `context doctor` to check whether the profile/context pack is missing major signals or stale.

## Git Version Management

Use:

```bash
python scripts/main.py git sync
```

The command stages `_index/openclaw_memory_index.json`, `03-Reference/OpenClaw记忆索引.md`, `02-Lessons/OpenClaw-Daily/`, and permanent memory files, then commits and pushes from the Obsidian vault repository.
