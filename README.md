# Memory Sync Skill

> A local-first memory layer that turns agent conversations into an Obsidian-backed, Git-versioned, cross-agent knowledge base.

[![Version](https://img.shields.io/badge/version-v1-blue)](#)
[![Local First](https://img.shields.io/badge/local--first-yes-brightgreen)](#)
[![Obsidian](https://img.shields.io/badge/storage-Obsidian-purple)](#)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

Memory Sync helps AI agents remember at the right time, understand the user better, and carry useful context across tools like OpenClaw, Codex, Claude, OpenCode, hermes-agent, and Qoder.

It is built as a companion to OpenClaw, not a replacement. OpenClaw can continue doing slower recall, dreaming, and long-term promotion. Memory Sync adds the fast working layer: preserve useful context early, make it searchable in Obsidian, reinforce it when used, and forget it when it stops mattering. By default, the current agent reviews candidate memories itself; the script prepares evidence and safely applies structured decisions.

Detailed commands and operating rules live in [SKILL.md](SKILL.md). This README focuses on what the project does and why it exists.

## 中文简介

> 一个本地优先的 agent 记忆层，把对话、项目交接和用户偏好沉淀成 Obsidian 知识库，并支持 Git 版本管理和多 agent 迁移。

Memory Sync 解决的是一个很具体的问题：agent 不是完全没有记忆，而是经常不能在需要的时候用上正确的上下文。

它作为 OpenClaw 的伴侣层，不替代 OpenClaw 原有的 recall、dreaming 和长期记忆沉淀，而是补上更快的一层：先保存有价值的记忆，让它马上进入可检索、可理解、可交接的工作层；之后再通过使用强化和 TTL 遗忘，让真正有用的留下。默认情况下，当前调用 skill 的 agent 会亲自审核候选记忆；脚本只负责准备证据、校验结构和安全落库。

具体命令、配置和执行流程写在 [SKILL.md](SKILL.md)。README 只介绍产品作用和基本逻辑。

## Why It Exists

Agent memory often fails in three quiet ways:

| Problem | What Usually Happens | What Memory Sync Adds |
| --- | --- | --- |
| Memory is too late | Useful context may only appear after slow long-term distillation | Preserve it early and make it searchable immediately |
| Memory is too hidden | Users cannot easily inspect, correct, or own what the agent remembers | Store memory as readable Markdown and JSON in Obsidian |
| Memory is too local | Switching agents means re-explaining the same background | Export compact shared context for multiple agents |
| Memory judgment is uncertain | Rules often overfit generic keywords or miss subtle lessons | Let the current agent review candidates while scripts enforce evidence and file safety |

Memory Sync is built for the middle layer between raw chat history and permanent memory:

```text
preserve first -> use while fresh -> reinforce if useful -> forget if unused
```

## 为什么需要它

很多 agent 记忆系统的问题不是“完全没记忆”，而是“记忆出现得太晚、藏得太深、迁移成本太高”。

| 问题 | 常见结果 | Memory Sync 的补位 |
| --- | --- | --- |
| 记忆太晚 | 长期沉淀完成时，最佳使用窗口已经过去 | 先保存有价值的上下文，立刻进入可检索层 |
| 记忆太隐蔽 | 用户很难检查、修正、迁移 agent 记住了什么 | 把记忆写进 Obsidian，变成可读、可链接的资产 |
| 记忆太局部 | 换一个 agent 就要重新解释背景 | 输出多 agent 可共享的精简上下文 |
| 判断太不确定 | 纯规则容易误收通用词，或漏掉纠正、失败教训这类高价值内容 | 让当前 agent 审核候选，脚本负责证据和文件边界 |

Memory Sync 关注的是“原始聊天”和“永久记忆”之间的中间层：

```text
先保存 -> 趁新鲜时使用 -> 有用就强化 -> 没用就遗忘
```

## What It Solves

| Value | How It Helps |
| --- | --- |
| OpenClaw remembers sooner | Copies daily memory and distilled candidates into an Obsidian working layer before long-term promotion finishes |
| OpenClaw understands the user better | Builds an evidence-backed user profile from repeated preferences, projects, boundaries, and decisions |
| Memory becomes a personal knowledge base | Turns useful agent collaboration into Markdown, source links, JSON indexes, and Git/GitHub history |
| Agent switching becomes cheaper | Keeps per-agent lanes separate while publishing shared portable context |
| Agent capabilities become visible | Syncs installed skills into a personal capability inventory so agents know what tools are available |
| OpenClaw gets a complementary rhythm | Lets OpenClaw keep slow deep memory while Memory Sync handles early preservation, use, reinforcement, and forgetting |

## 它解决什么

| 价值 | 作用 |
| --- | --- |
| 让 OpenClaw 更早记得住 | 每日记忆和 OpenClaw 筛出的候选记忆先进入 Obsidian 工作层，不必等长期晋升完成 |
| 让 OpenClaw 更容易听懂用户 | 从反复出现的偏好、项目、边界和决定中动态绘制用户画像 |
| 打造自己的记忆知识库 | 把 agent 协作中的有效经验变成 Markdown、源链接、JSON 索引和 Git/GitHub 历史 |
| 降低 agent 切换成本 | 各 agent 保留自己的本地记录，同时共享一份提炼后的通用上下文 |
| 用“先记忆再遗忘”辅助 OpenClaw | OpenClaw 做更慢更深的长期沉淀，Memory Sync 做更早保存、更快使用和按 TTL 遗忘 |

## Core Model

Memory Sync has four layers:

| Layer | Purpose |
| --- | --- |
| Source | Reads OpenClaw daily files, OpenClaw distilled candidates, agent handoffs, project captures, USER.md, and local agent configuration |
| Obsidian | Provides the human-readable memory surface with Markdown pages, dashboards, source links, and reviewable profile output |
| Index and Retention | Maintains the machine-readable memory index, S1-S4 stages, hit reinforcement, TTL expiry, and safe cleanup |
| Shared Context | Publishes compact context packs under `_shared/context/` for Codex, Claude, OpenClaw, OpenCode, hermes-agent, and Qoder |
| Personal Knowledge | Preserves non-daily knowledge such as MEMORY.md, AGENTS.md, USER.md, and installed skill inventories under `Personal/Agent Knowledge/` |

OpenClaw source files are treated as read-only. Memory Sync works on Obsidian copies and derived outputs.

## Memory Lifecycle

```text
OpenClaw / agent context
        |
        v
Obsidian working memory
        |
        v
Index + profile + shared context
        |
        v
Use reinforces, disuse expires
```

Retention is intentionally practical:

| Stage | Meaning |
| --- | --- |
| S1 | Fresh preserved memory |
| S2 | Used once or backed by a recall signal |
| S3 | Repeatedly useful or distilled by OpenClaw |
| S4 | Permanent memory |

High-value process memories, including successful procedures, corrections, failure lessons, and explicit user rules, start at S2 because they calibrate future agent behavior.

## What Makes It Different

- It preserves memory before deciding whether it deserves long-term storage.
- It treats Obsidian as a first-class memory console, not just a backup folder.
- It separates per-agent raw context from shared distilled context.
- It preserves non-daily agent knowledge and installed skill lists as part of the user's portable knowledge base.
- It keeps profile claims evidence-backed.
- It supports forgetting as a product feature, not a failure.
- It helps multiple agents understand the same user without forcing them into one runtime.

## Supported Agents

| Agent | Role |
| --- | --- |
| OpenClaw | Source memory, recall/dreaming candidates, long-term promotion |
| Codex | Engineering handoff and project-state capture |
| Claude | Long-context writing, reasoning, and handoff summaries |
| OpenCode | Code-agent context portability |
| hermes-agent | Agent-to-agent handoff context |
| Qoder | Explicit handoff and shared context portability while local chat schemas remain experimental |

## Relationship To OpenClaw

OpenClaw and Memory Sync form a two-speed memory system:

| OpenClaw | Memory Sync |
| --- | --- |
| Slower recall, dreaming, and promotion | Faster preservation, indexing, and reuse |
| Finds deeper long-term candidates | Keeps fresh context available early |
| Maintains its own source memory | Copies useful memory into Obsidian without editing the source |

## Platform Notes

Memory Sync is local-first and uses Python standard library APIs. It is expected to work on Windows, macOS, and Linux when Python, Git, an OpenClaw workspace, and an Obsidian vault path are available.

Obsidian does not need to be running. The script writes Markdown and JSON files directly to the vault.


## Current Release

- Added high-value process memories: success patterns, corrections, failure lessons, and user rules start at S2.
- Added personal knowledge sync for non-daily agent knowledge such as MEMORY.md, USER.md, AGENTS.md, and TOOLS.md.
- Added installed skill inventory sync under `_shared/agent_skills.json`, `_agents/<agent>/skills.json`, and `Personal/Agent Knowledge/Agent Skills.md`.
- Added operating contracts for OpenClaw and hermes-agent context exports.
- Added agent-assisted review mode: the current agent reviews candidate memories, while scripts prepare evidence and apply structured decisions.
- Added readable conversation archives for supported local logs; archived conversations enter review before becoming memories.
- Added stricter review grounding checks and read-only behavior for diagnostic context commands.

## 当前版本

- 新增高价值过程记忆识别：成功步骤、纠正步骤、失败教训、用户约定直接从 S2 起步。
- 新增非每日长期知识同步：同步 MEMORY.md、USER.md、AGENTS.md、TOOLS.md 到 `Personal/Agent Knowledge/`。
- 新增已安装 skill 清单同步，输出到 `_shared/agent_skills.json`、`_agents/<agent>/skills.json` 和 `Personal/Agent Knowledge/Agent Skills.md`。
- 为 OpenClaw 和 hermes-agent 上下文加入 Operating Contract，强化规则读取、冲突反馈和安全边界。
- 新增 agent-assisted review 模式：当前 agent 负责审核候选记忆，脚本负责准备证据和结构化落库。
- 新增本地对话归档能力；归档对话先进入 review，再决定是否晋升为记忆。
- 新增更严格的证据校验，并让上下文诊断类命令保持只读。

## Documentation

- [SKILL.md](SKILL.md): commands, workflows, trigger logic, configuration, and operating rules.
- [config/](config): configurable filters, keywords, and trigger words.
- [.env.example](.env.example): local path and sync configuration template.

## License

MIT
