# Memory Sync Skill

> Stop re-explaining yourself to every agent.
>
> Memory Sync turns OpenClaw, Codex, Claude, OpenCode, Hermes, Qoder, and other agent conversations into an Obsidian + Git memory layer you own.

[![Version](https://img.shields.io/badge/version-v1-blue)](#)
[![Local First](https://img.shields.io/badge/local--first-yes-brightgreen)](#)
[![Obsidian](https://img.shields.io/badge/storage-Obsidian-purple)](#)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

Agent memory should not vanish when a chat ends, hide inside one runtime, or force you to repeat the same context every morning.

Memory Sync is a local-first skill that preserves useful context early, lets the current agent review what deserves to become memory, keeps it readable in Obsidian, reinforces it when used, and forgets it when it stops mattering.

```text
Chat -> Preserve -> Review -> Promote -> Reuse / Forget
```

In one line:

```text
Remember first. Forget by disuse. Own the memory.
```

## 中文简介

不要再一遍遍给 Agent 解释你是谁、项目做到哪、上次踩过什么坑。

Memory Sync 把 OpenClaw、Codex、Claude、OpenCode、Hermes、Qoder 等 Agent 的聊天、候选记忆、项目交接、用户偏好和技能清单沉淀到 Obsidian + Git，变成你自己可查看、可追溯、可迁移的个人记忆知识库。

核心原则：

```text
先记住，再遗忘；用进废退；记忆归你。
```

## The Problem

Most agent memory fails in a very ordinary loop:

```text
New chat -> Explain context -> Agent helps -> Session ends -> Context disappears
```

Then the next agent, next window, or next day starts cold again.

| Pain | What happens | What Memory Sync changes |
| --- | --- | --- |
| Memory arrives too late | Useful context only appears after slow long-term distillation | Preserve fresh context immediately |
| Memory is hidden | The user cannot inspect or correct what the agent remembers | Store readable Markdown in Obsidian |
| Memory is trapped | Switching agents means explaining everything again | Export portable context for multiple agents |
| Memory quality is uncertain | Rules miss subtle lessons or over-collect routine noise | Let the current agent review candidates while scripts enforce evidence and safety |

## What Memory Sync Does

Memory Sync adds a fast working-memory layer beside your agents.

```text
OpenClaw / Codex / Claude / Hermes / Qoder
        |
        v
Memory Sync review and retention layer
        |
        v
Obsidian readable memory + Git version history
        |
        v
Portable context for the next agent
```

It can:

- copy OpenClaw daily memory into an Obsidian working layer without editing the source
- import OpenClaw recall, dreaming, and promoted memory candidates
- archive local Codex, Claude, OpenClaw, and Hermes conversations as traceable evidence
- preserve non-daily knowledge such as `MEMORY.md`, `USER.md`, `AGENTS.md`, and installed skill inventories
- build `Dashboard/User Profile.md` from evidence-backed preferences, boundaries, projects, and decisions
- export `Context/agent_brief.md` and adapter context for agent switching
- maintain S1-S4 memory stages, TTL, hit reinforcement, and safe cleanup
- keep machine-readable state under `.memory-sync/` while keeping human review in Markdown
- sync memory assets through Git when you explicitly ask it to

## Why It Is Different

Memory Sync is not trying to replace OpenClaw memory.

It gives OpenClaw and other agents a faster layer:

| OpenClaw | Memory Sync |
| --- | --- |
| Slower recall, dreaming, and long-term promotion | Fast preservation, indexing, and reuse |
| Finds deeper candidates over time | Keeps fresh context available while it is still useful |
| Maintains its own source memory | Copies useful memory into Obsidian without touching the source |

The product rhythm is different:

```text
OpenClaw: distill first, use later
Memory Sync: preserve first, use now, forget later if unused
```

## Core Outputs

Memory Sync writes a vault that is useful for both humans and agents:

| Output | Purpose |
| --- | --- |
| `Dashboard/Memory Directory.md` | Clean Obsidian navigation for memory, profile, skills, and portable context |
| `Dashboard/Memory Index.md` | Human-readable memory index with stages and source links |
| `Dashboard/Memory Dashboard.md` | Memory counts, stage distribution, and shared-memory snapshot |
| `Dashboard/User Profile.md` | Evidence-backed dynamic user profile |
| `Context/agent_brief.md` | Compact cross-agent context for handoff |
| `Memories/memory_*.md` | Stable memory cards with frontmatter and source trace links |
| `Sources/<agent>/...` | Source evidence such as daily memory copies, conversation summaries, and handoffs |
| `Personal/Agent Knowledge/` | Agent rules, long-term notes, and installed skill inventories |
| `.memory-sync/index/memory_index.json` | Machine source of truth |

## Memory Lifecycle

Memory Sync keeps memory practical, not sentimental.

| Stage | Meaning |
| --- | --- |
| S1 | Fresh preserved memory |
| S2 | Used once, backed by a recall signal, or identified as high-value process memory |
| S3 | Repeatedly useful or distilled by OpenClaw |
| S4 | Permanent memory |

High-value process memories start at S2 when they capture:

- successful procedures
- corrections from the user
- failure lessons
- explicit user rules
- reusable project decisions

Routine health checks, repeated status pings, transient logs, and low-value tool noise should be discarded during review.

## Supported Agents

| Agent | Role |
| --- | --- |
| OpenClaw | Source memory, recall/dreaming candidates, session evidence, long-term promotion companion |
| Codex | Local conversation archive, engineering handoff, project-state capture |
| Claude | Local conversation archive, long-context writing, reasoning, and handoff summaries |
| OpenCode | Code-agent context portability |
| hermes-agent | Local SQLite conversation archive, installed skill inventory, handoff context |
| Qoder | Explicit handoff and shared context portability while local chat schemas remain experimental |

## Use This If

- you use OpenClaw, Codex, Claude, or multiple agents across projects
- you keep repeating the same background to agents
- you want agent memory to be readable in Obsidian
- you want Git/GitHub history for your personal memory knowledge base
- you want a local-first system instead of a cloud memory service

Do not use it if you want a hosted SaaS memory layer, do not want local files, or do not want agents to review candidate memories.

## First Run

Detailed commands and operating rules live in [SKILL.md](SKILL.md). The shortest path is:

```bash
python scripts/main.py review prepare
# current agent reviews .memory-sync/review/latest-pack.json
python scripts/main.py review apply decisions.json
python scripts/main.py status
```

Optional:

```bash
python scripts/main.py conversations scan codex --date YYYY-MM-DD
python scripts/main.py conversations scan openclaw --date YYYY-MM-DD
python scripts/main.py context export all
python scripts/main.py skills sync
python scripts/main.py git sync
```

## Platform Notes

Memory Sync is local-first and uses Python standard library APIs. It is expected to work on Windows, macOS, and Linux when Python, Git, an OpenClaw workspace, and an Obsidian vault path are available.

Obsidian does not need to be running. The script writes Markdown and JSON files directly to the vault.

## Current Release

- Added high-value process memories: success patterns, corrections, failure lessons, and user rules start at S2.
- Added personal knowledge sync for non-daily agent knowledge such as `MEMORY.md`, `USER.md`, `AGENTS.md`, and `TOOLS.md`.
- Added installed skill inventory sync under `.memory-sync/shared/agent_skills.json`, `.memory-sync/agents/<agent>/skills.json`, and `Personal/Agent Knowledge/Agent Skills.md`.
- Added operating contracts for OpenClaw and hermes-agent context exports.
- Added agent-assisted review mode: the current agent reviews candidate memories, while scripts prepare evidence and apply structured decisions.
- Added readable conversation archives for Codex, Claude, OpenClaw, and Hermes local logs; archived conversations enter review before becoming memories.
- Added stricter review grounding checks and read-only behavior for diagnostic context commands.
- Added `Dashboard/Memory Directory.md` as a clean human navigation page without placeholder README links.

## 当前版本

- 新增高价值过程记忆识别：成功步骤、纠正步骤、失败教训、用户约定直接从 S2 起步。
- 新增非每日长期知识同步：同步 `MEMORY.md`、`USER.md`、`AGENTS.md`、`TOOLS.md` 到 `Personal/Agent Knowledge/`。
- 新增已安装 skill 清单同步：输出到 `.memory-sync/shared/agent_skills.json`、`.memory-sync/agents/<agent>/skills.json` 和 `Personal/Agent Knowledge/Agent Skills.md`。
- 为 OpenClaw 和 hermes-agent 上下文加入 operating contract，强化规则读取、冲突反馈和安全边界。
- 新增 agent-assisted review 模式：当前 agent 负责审核候选记忆，脚本负责准备证据和结构化落库。
- 新增 Codex、Claude、OpenClaw、Hermes 本地对话归档能力；归档对话先进入 review，再决定是否晋升为记忆。
- 新增更严格的证据校验，并让上下文诊断类命令保持只读。
- 新增 `Dashboard/Memory Directory.md` 人类导航页，不再用占位 README 伪装目录。

## Documentation

- [SKILL.md](SKILL.md): commands, workflows, trigger logic, configuration, and operating rules.
- [config/](config): configurable filters, keywords, and trigger words.
- [.env.example](.env.example): local path and sync configuration template.

## License

MIT
