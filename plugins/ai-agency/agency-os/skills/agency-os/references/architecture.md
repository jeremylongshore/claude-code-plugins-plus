## Harness compatibility

This SKILL.md is the authoritative spec and is harness-agnostic. The slash-command interface (`/agency-os ...`), the status flow, the schema, the workspace layout, and every command's behavior are the same everywhere.

Per-harness wrappers only differ in two things:

- **How commands are triggered.** Claude Code exposes them as real slash commands via the plugin manifest. Cursor / Cline / generic MCP harnesses load this file as instructions and rely on the user typing `/agency-os ...` (or the natural-language equivalent) into chat. Either way, the parser is the same.
- **Whether mutations are delegated to a subagent.** The "Execution model" section below describes Claude Code's Haiku subagent dispatch. Other harnesses run mutations directly on the main agent. The Notion MCP calls underneath are identical; only the indirection changes.

See `docs/harnesses/` for per-harness setup. If you're reading this in a non-Claude-Code harness, treat the subagent dispatch instructions as optional: execute commands inline instead.

## Execution model — model selection by harness

### Claude Code: delegate to Sonnet (medium reasoning) for mutations, orchestrator picks for batch execution

Every `/agency-os <command>` invocation runs on **Sonnet at medium reasoning effort** via a subagent, not on the orchestrator's model. The work this skill does — resolve an ID, mutate a Notion row via MCP, format a brief — needs enough judgment (dedup checks, brief assembly, dependency reasoning) that Haiku slipped on edge cases; Sonnet at medium effort is the right balance of accuracy and cost. The orchestrator stays free for the conversation around the command.

When the user invokes `/agency-os <command> <args>` (or the orchestrator translates a natural-language request into one — see "Natural-language driving" below), the orchestrator's only job is to dispatch:

```
Agent({
  description: "Run /agency-os <command>",
  subagent_type: "general-purpose",
  model: "sonnet",
  prompt: "Run the agency-os skill for: /agency-os <command> <args>.\n\nUse medium reasoning effort — think through ID resolution, dedup checks, and brief assembly carefully, but don't over-deliberate on mechanical mutations.\n\nRead .claude/skills/agency-os/SKILL.md and execute that exact command end-to-end: sync preflight (call notion-fetch live — never read from any local cache file), resolve IDs against the live Notion result, mutate Notion via the Notion MCP, and return the same output format the skill specifies (the brief for `start`, the `+ Suggestion: ... -> url` line for `suggest`, etc.). All task/result links must be formatted as CommonMark markdown links — `title` — never HTML `<a>` tags and never a bare URL. Claude Code renders markdown but not HTML, so HTML anchors show up as literal text. If the command is `start`, also emit the full kickoff brief verbatim. If anything fails (sync, MCP call, ID resolution), stop and report — do not guess.\n\nYOU MUST ALWAYS PRODUCE OUTPUT. Never return silently. On success: the skill's standard output. On failure: one paragraph describing exactly what failed, what was attempted, and what state Notion was left in. Returning nothing is not an option."
})
```

**The orchestrator MUST always relay the subagent's result to the user — no exceptions.**

- If the subagent produced output: pass it through verbatim.
- If the subagent returned empty output or no output at all: say so explicitly — `subagent returned no output; execution status unknown. Check Notion directly.`
- Never absorb the result silently. Never say "I don't have information about what happened." If you don't know, say you don't know and tell the user to check Notion.

Do **not** re-run any step yourself, do not "double-check" the subagent's work.

**Natural-language driving stays on the orchestrator.** Parsing "let's discuss the X task" into `/agency-os discuss <id>`, asking the user clarifying questions during a discussion, deciding when to call `log` vs `add-subtask` — that conversation runs on the orchestrator so thread context survives across turns. Only the discrete mutation (each `log`, each `add-subtask`, each `approve`) dispatches to the Sonnet subagent.

Rule of thumb: anything that touches Notion via the MCP -> Sonnet subagent. Anything that's deciding *what* to touch -> orchestrator.

### Non-Claude harnesses: read models from config.json

On Cursor, Cline, Continue, and generic MCP harnesses, the skill can't spawn subagents. Instead:

1. **Before first use:** run `/agency-os init` to store your preferred models in `.claude/skills/agency-os/config.json`.
2. **Mutations (suggest, discuss, log, etc.):** run inline on the main agent.
3. **Batch execution (`/agency-os run`):** read `config.json` and use the stored models' constraints when evaluating task complexity.

The config file has this shape:

```json
{
  "harness": "cursor",
  "models": {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-7"
  }
}
```

The `/agency-os run` command still uses the same picker heuristic (Haiku for mechanical work, Sonnet default, Opus for strategic) — but on non-Claude harnesses, you need to ensure your harness has an API or SDK integration with those models (e.g., via the Anthropic SDK in a Continue custom tool). If your harness only supports one model, set all three to that model and the skill will use it for everything.

---

## What lives where (hybrid contract)

This skill is the one place where the project's local-vs-Notion split is enforced. Get this wrong and you either spam MCP tokens reading what should be a file, or you put mutable state somewhere git can't roll it back.

- **Local, in this repo, source-of-truth:** every skill spec under `.claude/skills/`, every doc under `docs/`, the `notion-pointers.json` binding, and `references/general-guidance.md` (the canonical General Guidance text — Notion's page is a one-way mirror). Agents read these directly off disk — fast, free, greppable, diffable.
- **In Notion, source-of-truth:** task rows (Title / Status / Corpus / Priority / Impact / Type / Cadence / Effort / Parent Task), discussion logs, done logs, corpus pages (Goal + local guidance the operator authors), and the Hub itself with its DB views. Anything the operator wants to review-in-place, anything that changes frequently, anything that doesn't benefit from `git log`.
- **One-way mirror, not two-way:** `references/general-guidance.md` -> Notion General Guidance page is the only sync direction. Edit the local file, then push to Notion (via `scaffold` or a manual `update`). Never edit the Notion page and try to reverse-sync it; drift will follow.

When this skill assembles a brief for an agent, it pulls **task state** from Notion (the row, the discussion log, subtask titles) and **stable spec** from local files (general guidance, corpus local guidance if those are mirrored, links into `docs/` and `.claude/skills/`). The brief contains pointers to local files, not copies of them, so the agent can grep further when it needs to.

```
# setup
/agency-os scaffold [--parent=<page-id-or-url>] [--corpora="<n1>,<n2>,..."]
                                                          # idempotent: builds the full Notion workspace from scratch (Hub, Tasks DB, corpus pages, views). No Notion template duplication required.
/agency-os init [--harness claude-code|cursor|cline|continue|generic-mcp] [--haiku=<model>] [--sonnet=<model>] [--opus=<model>]
                                                          # configure model selection (non-Claude harnesses only; Claude Code ignores this)
/agency-os sync                                           # preflight: verify live Notion connection and pointer IDs

# suggestions
/agency-os suggest "<title>" [--corpus=<s>] [--type one-time|recurring]
                              [--cadence daily|weekly|biweekly|monthly|quarterly|yearly]
                              [--notes "..."] [--effort S|M|L|XL]

# clarification & subtasks
/agency-os discuss <id>                                   # Suggestion -> Discussion + load context for clarification
/agency-os log <id> "<entry>"                             # append a discussion entry
/agency-os add-subtask <parent-id> "<title>" [--effort=<e>] [--notes "..."] [--deps=<id1>,<id2>,...]
/agency-os approve <id>                                   # Discussion -> To-Do; cascades active subtasks

# execution
/agency-os start <id>                                     # To-Do -> In Progress + emit kickoff brief
/agency-os refresh                                        # auto-enumerate Status=To-Do AND Exec=Agent via Notion REST API, write state/todo-ids.json
/agency-os run [--go]                                     # batch-execute the To-Do sidecar; orchestrator picks model per task
/agency-os done <id> [--result-link <url>] [--note "..."]
/agency-os kill <id> [--reason "..."]

# read
/agency-os next [N] [--corpus=<s>]
/agency-os status
/agency-os list <suggestion|discussion|todo|inprogress|done|killed|recurring|all> [--corpus=<s>]
/agency-os show <id> [--section description|discussion|donelog|all] [--entry <date>]

# escape hatches
/agency-os update <id> [--title="..."] [--notes="..."] [--priority=1|2|3|4]
                       [--effort=S|M|L|XL]
                       [--type=one-time|recurring] [--cadence=...] [--corpus=<s>]
                       [--deps=<id1>,<id2>,...|none]
/agency-os move <id> --to <status>                        # force any status transition
/agency-os add-corpus "<name>" [--goal "..."]
```

**Natural language is also a trigger.** When the user says "add a suggestion to ...", "let's discuss the X task", "log: agreed to ...", "add a subtask: ...", "approve that", "make weekly task recurring", "mark X done with link <url>", "kill the Y idea" — the skill mutates Notion the same way it would for the slash command equivalent. The slash commands are the canonical interface; natural language is a convenience layer.

---

## Status flow — the dedup gate

```
Suggestion --discuss--> Discussion --approve--> To-Do --start--> In Progress --done--> Done
                                                                             ^
   any  --kill-->  Killed  (terminal)                                        |
                                                                             |
                              Recurring tasks: done logs an occurrence and   |
                              loops back to To-Do with Last Done updated. ---+
```

| Status | Meaning | Set by |
|---|---|---|
| `Suggestion` | Idea in the inbox; not yet discussed | `suggest`, manual Notion add |
| `Discussion` | Under clarification; subtasks may be emerging; not yet approved | `discuss` |
| `To-Do` | Approved scope; scheduled to execute | `approve`, recurring loop on `done` |
| `In Progress` | An agent is actively working it; brief has been emitted | `start` |
| `Done` | Closed (one-time only) | `done` (when `Type=one-time`) |
| `Killed` | Intentionally dropped | `kill` |

The picker filters on `Status == "To-Do"`, prioritising `1` then `2` then `3` then `4` then unset, and within that by Created ascending. The launcher requires `Status == "To-Do"`. The suggestor refuses dupes against any non-terminal status by Title-Jaccard >= 0.8.

If `start` crashes, the row sits at In Progress. Manual recovery: `/agency-os move <id> --to todo` or flip Status in Notion directly.

---

## Sync — preflight on every command

Before every command, call `notion-fetch <tasks_data_source_id>` (from `notion-pointers.json`) to get live data from Notion. Resolve `<id-or-substring>` against the live result. Never read from `notion-cache.json` or any local snapshot. Mutations also target Notion directly.

If `notion-fetch` fails (Notion API down, OAuth expired), print `sync failed: <reason>` and abort — do not fall back to any cached file.

---

## Workspace structure

```
Hub  (page)
+-- intro: what this board is for
+-- General Guidance  -> page
+-- General Plan      -> table; one row per Corpus, linked to its page
+-- Suggestions Inbox  (linked DB view: Status=Suggestion, sort Created desc)
+-- In Discussion      (linked DB view: Status=Discussion, sort Created desc)
+-- To-Do (Scheduled)  (linked DB view: Status=To-Do, sort Priority asc, group by Corpus)
+-- Recurring          (linked DB view: Type=recurring, sort Last Done asc)
+-- In Progress        (linked DB view: Status=In Progress)
+-- Recently Done      (linked DB view: Status=Done, sort Done At desc, limit 25)
+-- Resources          -> page

Tasks  (database)
+-- one row per task, of any status, including subtasks
```

### Tasks database schema

| Property | Type | Notes |
|---|---|---|
| `Title` | title | Imperative phrase, <=80 chars |
| `Status` | status | `Suggestion`, `Discussion`, `To-Do`, `In Progress`, `Done`, `Killed`. Default `Suggestion` |
| `Type` | select | `one-time` (default), `recurring` |
| `Cadence` | select | `daily`, `weekly`, `biweekly`, `monthly`, `quarterly`, `yearly`. Empty for `one-time` |
| `Last Done` | date | Set on `done` for recurring |
| `Corpus` | select | One of the configured corpora |
| `Priority` | select | `1`, `2`, `3`, `4` — **urgency** (1 = blocks something this week / 2 = this month / 3 = this quarter / 4 = nice to have / default). Lower number = higher urgency. Default `4` |
| `Impact` | select | `low`, `medium`, `high`, `outsized` — outcome size **within the task's corpus**, independent of urgency. Default `medium` |
| `Effort` | select | `S`, `M`, `L`, `XL`. Default `M` |
| `Exec` | select | `none` (default), `Agent`, `Human`. Operator-set gate: only `Agent`-marked To-Do rows enter the `run` queue |
| `Parent Task` | relation (self) | Set on subtasks; empty for top-level tasks |
| `Subtasks` | rollup | Auto-rolled from inverse of Parent Task; surfaces count |
| `Created` | created_time | Automatic |
| `Done At` | date | Set on terminal `Done` (one-time) |
| `Result Link` | url | Live link, post URL, PR URL, etc. |
| `Tags` | multi_select | Cross-cutting concerns (user-defined) |
| `Dependencies` | relation (self) | IDs of tasks that must reach `Done` before this row is dispatchable. Used only by `run` to stage execution; ignored by `start`, `next`, `list`. Empty by default |

### Task page body

Every task page uses **toggleable H2 sections** so the DB grid stays clean and details fold on click. Created via Notion's `is_toggleable: true` heading flag (Notion API). If the MCP path can't set the flag, fall back to plain H2; the user can toggle manually.

```
> Launch this task
> Paste in Claude Code: `/agency-os start <id>`

Description     <- starts expanded
   <freeform: what to do, why, acceptance criteria, links to docs/skills>

Subtasks        <- starts expanded if any subtasks exist, else hidden
   (linked DB view: Parent Task = this, sort Created asc)

Discussion log  <- starts collapsed
   ### 2026-01-10 — initial clarification
   Q: ...
   A: ...
   Decisions:
   - ...

Done log        <- starts collapsed; only meaningful for recurring
   ### 2026-01-12: completed by agent — link <url>

Related         <- starts expanded; one-line each
   Corpus: -> <corpus>
   General guidance: -> Guidance
   Parent: -> <parent-title>   <- only for subtasks
```

### Corpus pages

```
# Corpus: <name>

## Goal
1-3 sentences on what "done" looks like for this whole corpus.

## Local guidance
Conventions, owners, references. Anything an agent needs before its first task here.

## Tasks
(linked DB view: Corpus = this, group by Status)
```

### General Guidance page

Project-wide rules: link into `docs/`, link into `.claude/skills/`, the launch flow, house style. Kept short. Links beat duplication. Seeded from `references/general-guidance.md` — edit the local file, push the mirror.

---

## Pointer + cache files

`.claude/skills/agency-os/references/notion-pointers.json` (committed):

```json
{
  "hub": { "page_id": "<uuid>", "url": "...", "title": "..." },
  "tasks_database": {
    "database_id": "<uuid>",
    "data_source_id": "<uuid>",
    "url": "...",
    "task_id_prefix": "OS"
  },
  "guidance": { "page_id": "<uuid>", "url": "...", "title": "..." },
  "resources": { "page_id": "<uuid>", "url": "...", "title": "..." },
  "corpora": {
    "General": { "page_id": "<uuid>", "url": "...", "title": "General" }
  },
  "hub_views": { "Suggestions Inbox": "view://<uuid>", ... },
  "corpus_views": { "General": "view://<uuid>" },
  "schema_summary": { ... }
}
```

---
