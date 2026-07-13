# General Guidance

This is the **agency control plane** for your workspace. The Tasks database wrapped by this Hub is the single source of truth for everything the operator and agents work on together.

Customize this page with your project's own conventions, links, and rules. The skeleton below is a starting point.

## The flow

```
Suggestion -> Discussion -> To-Do (Scheduled) -> In Progress -> Done
                                                            (Killed = terminal drop, anywhere)
```

- **Suggestion** — raw idea. Anyone (operator, agent) can drop one in.
- **Discussion** — operator opens it for clarification. Agent asks questions. Each round is logged. Subtasks may emerge.
- **To-Do** — operator approved the scope. Scheduled to execute. Cascades active subtasks.
- **In Progress** — agent picked it up via `/agency-os start <id>`. Brief was loaded.
- **Done** — closed (one-time). For recurring tasks, "done" logs an occurrence and loops back to To-Do.
- **Killed** — dropped, kept for the record. Cascades to active subtasks.

## One-time vs recurring

Every task has a `Type`: `one-time` or `recurring`. Recurring tasks have a `Cadence` (daily / weekly / biweekly / monthly / quarterly / yearly) and a `Last Done` date that the skill updates automatically. The Hub's Recurring view surfaces them all; overdue recurring tasks float to the top of `next`.

## Subtasks

Subtasks are full Task rows with their `Parent Task` set. They have their own status, their own brief, their own discussion log. Approve cascade: when a parent moves Discussion -> To-Do, every active descendant follows. Kill cascade: same. Done is **not** cascaded — closing a parent does not auto-close subtasks (and vice versa); the skill only nudges.

## Brief assembly (overfeed protection)

When `/agency-os start <id>` runs, the agent's kickoff brief contains:

- Row properties (compact).
- Full **Description** body.
- Subtask titles + status (titles only, no bodies).
- The **single latest** Discussion log entry (older entries referenced by date for explicit lookup).
- Parent task's title + Description (one level only) for subtasks.
- Corpus: Goal + Local guidance.
- General Guidance (this page, full).

Older discussion entries, sibling tasks, other corpora, and the Done log are **not** included by default. They're loadable via `/agency-os show <id> --section discussion --entry <date>` when the agent needs more.

## Who works the board

- **Operator (the human user)** — drops suggestions, opens discussions, approves scope, dispatches starts via the Launch callout, marks done.
- **Agents (Claude Code sessions)** — read briefs, execute work using whatever skills/tools they need, log decisions, close with `done <id> --result-link <url>`.

## Natural-language driving

The skill responds to natural language. "Add a suggestion to ...", "let's discuss the X task", "log: agreed to ...", "add a subtask: ...", "approve it", "X is done with link <url>", "kill the Y idea" — all of these flow through the skill the same way the slash commands do.

## Project orientation

<!-- TODO: fill in your project root, docs, skills, and credential locations. Example:
- Project root: `C:\Work\my-project`
- Docs: `docs/`
- Skills: `.claude/skills/`
- Credentials: `.env` at repo root (gitignored)
-->

## Where information lives

The project runs on a **hybrid** local-vs-Notion split. When you need something, read from the right place:

- **Local files** (`.claude/skills/`, `docs/`, `.env`, etc.) are source-of-truth for stable spec: skill instructions, project docs, style guides. Free to read, git-tracked. Grep these.
- **Notion** is source-of-truth for mutable task state: the rows in the Tasks DB, their statuses, their discussion logs, their done logs, the corpus pages. Read these via the Notion MCP.
- This General Guidance page itself is a **one-way mirror** of `.claude/skills/agency-os/references/general-guidance.md`. The local file is canonical; the Notion copy exists so the operator sees the rules where the work lives. To change the rules, edit the local file and push the mirror.

## Launch flow

1. Open a To-Do task page in Notion.
2. Copy the line in the Launch callout (`/agency-os start <id>`).
3. Paste into Claude Code.
4. The skill flips status to In Progress, emits the brief, you execute.
5. Close: `/agency-os done <id> --result-link <url>`.
