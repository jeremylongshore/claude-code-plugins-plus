---
name: agency-os
description: |
  Notion-as-source-of-truth dispatch board for running your work like an AI agency.
  One Tasks database is the source of truth; tasks flow Suggestion through
  Discussion, To-Do, In Progress, and Done with subtasks, recurring cadences,
  dependencies, and template subtrees. Batch execution fans approved To-Do rows
  out to parallel agents with per-task model selection. Use when capturing chat
  to Notion, running the To-Do queue, suggesting, approving, or discussing tasks,
  or coordinating multi-task batches. Trigger with "/agency-os" subcommands or
  natural-language variants ("add a suggestion: …", "let's discuss X",
  "run the queue").
allowed-tools: Read, Write, Edit, Bash(python3:*), Bash(npx:*), Glob, Grep
version: 0.2.0
author: ratamaha-git <ratamaha@automatelab.tech>
license: MIT
compatibility: Designed for Claude Code; requires the Notion MCP server (@notionhq/notion-mcp-server) and a Notion workspace with a Tasks database
tags: [ai-agency, notion, orchestration, mcp, dispatch, parallel-execution]
---

# agency-os

Notion-as-source-of-truth dispatch board. One Tasks database, one Hub page, one
page per Corpus, one page each for General Guidance and Resources. The skill
mutates Notion via the Notion MCP (`mcp__*__notion-*` tools); only
`references/notion-pointers.json` is committed to git.

**Skill name decision:** the skill is named `agency-os` (matching the repo). All
commands are `/agency-os <cmd>`. This is the single plugin entry point; there
is no `agency-os/notion` sub-namespace. If you embed this plugin alongside
others, prefix commands with `agency-os` to avoid collisions.

## Overview

agency-os turns a single Notion database into a multi-status dispatch board for
AI work. The model is intentionally narrow:

- **One Tasks database** is the source of truth for status, priority, model
  selection, and ownership. No parallel kanban tools.
- **One Hub page** holds the General Guidance, Resources, and Corpus pointers
  that every task consults.
- **Tasks flow through five statuses**: Suggestion → Discussion → To-Do →
  In Progress → Done. The dedup gate at each transition prevents accidental
  re-execution.
- **`run`** fans approved To-Do rows out to parallel agents. Each task carries
  its own model selection (Haiku for cheap fan-out, Sonnet for default,
  Opus for hard reasoning) and respects declared dependencies.

The skill is **stateless on disk** — the only committed artifact is
`references/notion-pointers.json` (database/page IDs). All runtime state lives
in Notion.

For the full architecture (status flow, sync protocol, workspace structure,
pointer/cache format), see [`references/architecture.md`](references/architecture.md).

## Prerequisites

- **Notion MCP server installed**:
  `npx -y @notionhq/notion-mcp-server` (declare in `.mcp.json`)
- **Notion integration token** (`NOTION_TOKEN`) with read+write access to your
  workspace. Add `.env` to `.gitignore` — never commit the token.
- **A Notion Tasks database** with the columns the skill expects (see
  `references/architecture.md` § "Workspace structure" for the schema). The
  `/agency-os init` command can scaffold this for you.
- **Python 3** for the optional `scripts/query-tasks.py` helper.

First-time setup:

```bash
ccpi install agency-os
# then in Claude Code:
/agency-os init --harness=basic --haiku=cost-tier --sonnet=default --opus=hard-reasoning
```

## Instructions

The skill is a CLI surface over Notion. Three usage patterns:

1. **Direct command invocation** — `/agency-os <cmd> [args]`. See
   [`references/commands.md`](references/commands.md) for the full reference
   of 19 commands (`init`, `scaffold`, `suggest`, `discuss`, `log`,
   `add-subtask`, `approve`, `start`, `refresh`, `run`, `done`, `kill`,
   `next`, `status`, `list`, `show`, `update`, `move`, plus `launch` alias).

2. **Natural-language driving** — the skill translates conversational chat into
   the corresponding command. Examples in
   [`references/natural-language.md`](references/natural-language.md).

3. **Batch execution** — `/agency-os run [--go]` fans the entire To-Do queue
   out to parallel agents with per-task model selection. See `## Examples`
   below for the canonical flow.

Status flow is enforced — you cannot skip a stage. Every command performs a
sync preflight to ensure your local view of Notion is current (see
`references/architecture.md` § "Sync — preflight on every command").

When drafting any user-facing copy (READMEs, blog posts, launch surfaces),
apply the positioning brief at
[`references/positioning.md`](references/positioning.md) before writing.

## Output

Every command returns to chat with:

- **Verdict line** — `✅ <action>` or `⚠️ <reason>` (one line, scannable)
- **Affected task IDs and titles** — every task touched, with its new status
- **Next-action hint** — what command the operator would typically run next

Batch `run` additionally emits:

- A per-task pass/fail table
- Total model spend estimate (Haiku/Sonnet/Opus call counts)
- Outstanding-dependency callouts for tasks that couldn't start

## Error Handling

The skill fails closed on five well-defined cases (full details in
`references/architecture.md` § "Status flow — the dedup gate"):

| Condition | Behavior |
|---|---|
| Notion API auth fails | Halt, print "NOTION_TOKEN missing or invalid", exit 1 |
| Database/page ID drift (pointers stale) | Halt, print "Run `/agency-os refresh`", exit 1 |
| Status-flow violation (e.g. `approve` on a Suggestion) | Halt with the required prerequisite step quoted |
| Dependency cycle detected during `run` | Halt, list the cycle, exit 1 |
| Task missing required model selection | Halt, print "Run `/agency-os update <id> --model <tier>`" |

The skill never silently corrects state in Notion — every fix is an explicit
command the operator must run.

## Examples

Capture a chat insight as a Suggestion:

```text
User: add a suggestion: refactor the auth flow to use the new token cache
Skill: → /agency-os suggest "refactor the auth flow to use the new token cache"
       ✅ Created Suggestion #t-2026-05-23-001 in corpus "platform"
       Next: /agency-os discuss t-2026-05-23-001
```

Approve and run a batch:

```text
User: approve t-2026-05-23-{001..003} then run the queue
Skill: ✅ Approved 3 tasks → To-Do
       /agency-os run --go
       → fanning to 3 parallel agents...
       ✅ Done: 2 | ⚠️ Blocked on deps: 1 | Total spend: ~$0.04
```

More examples and the full command catalog are in
[`references/commands.md`](references/commands.md).

## Resources

- **Plugin source**: <https://github.com/ratamaha-git/agency-os>
- **Launch post**: <https://automatelab.tech/agency-os-launch/>
- **`references/architecture.md`** — status flow, sync protocol, workspace schema
- **`references/commands.md`** — full CLI reference (19 commands)
- **`references/natural-language.md`** — chat-to-command translation table
- **`references/positioning.md`** — canonical brief for user-facing copy
- **`references/general-guidance.md`** — shared operating principles applied to every task
- **`references/notion-pointers.json`** — pointer file scaffold (database/page IDs)
- **`references/task-page-template.md`** — Notion page template for new tasks
- **`references/corpus-template.md`** — Notion page template for a Corpus
- **`references/config-template.json`** — default per-task model routing
- **`scripts/query-tasks.py`** — optional Python helper for offline introspection
