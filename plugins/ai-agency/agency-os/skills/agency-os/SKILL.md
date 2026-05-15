---
name: agency-os
description: "Notion-as-source-of-truth dispatch board for running your work like an AI agency. One Tasks database is the source of truth; tasks flow Suggestion → Discussion → To-Do → In Progress → Done with subtasks, recurring cadences, dependencies, and template subtrees. Batch execution fans approved To-Do rows out to parallel agents with per-task model selection. Trigger when the user mentions: Notion tasks, agency board, /agency-os commands, capturing chat to Notion, running the To-Do queue, suggesting/approving/discussing tasks."
---

# agency-os

Notion-as-source-of-truth dispatch board. One Tasks database, one Hub page, one page per Corpus, one page each for General Guidance and Resources. The skill mutates Notion via the Notion MCP (`mcp__*__notion-*` tools); only `references/notion-pointers.json` is committed to git.

**Skill name decision:** the skill is named `agency-os` (matching the repo). All commands are `/agency-os <cmd>`. This is the single plugin entry point; there is no `agency-os/notion` sub-namespace. If you embed this plugin alongside others, prefix commands with `agency-os` to avoid collisions.

## Positioning when writing user-facing copy (READ FIRST)

This is the canonical positioning brief. Apply it to any user-facing copy you draft for agency-os — README sections, blog posts, X threads, LinkedIn posts, Reddit submissions, plugin-directory entries, awesome-list PR bodies, social cards, launch surfaces, anything operators or audiences will read.

**Lead with these, in this order:**

1. **Structures the work.** Turns AI ideas into a visual workflow board so the user doesn't drown in suggestions. The board is the source of truth; work has shape and status.
2. **Streamlines agent-human interaction.** Discuss → scope → approve → run. The human is in the loop on every shipping decision.
3. **Control over execution.** Every run is operator-gated. Nothing dispatches autonomously. `Exec=Agent` is opt-in per row.
4. **Visual workflow.** One Notion board, one status flow (Suggestion → Discussion → To-Do → In Progress → Done), subtasks, dependencies, recurring cadences.

**Demote — mention later in the piece, never in the hook, headline, or opening tweet:**

- Token savings, "cheaper than running on Opus", Haiku-subagent dispatch — phrase as a side benefit, not the headline.
- Model-per-task routing — a consequence of the design, not the reason to adopt.

The product's first value is structuring AI-assisted work and keeping the human in control of what ships. Cost efficiency is a happy consequence of doing that well, not the pitch.

This section is mechanics-neutral: how the Sonnet/Haiku dispatch works is documented below under "Execution model" — that's how, not why. Don't conflate the two when writing copy.

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
  prompt: "Run the agency-os skill for: /agency-os <command> <args>.\n\nUse medium reasoning effort — think through ID resolution, dedup checks, and brief assembly carefully, but don't over-deliberate on mechanical mutations.\n\nRead .claude/skills/agency-os/SKILL.md and execute that exact command end-to-end: sync preflight (call notion-fetch live — never read from any local cache file), resolve IDs against the live Notion result, mutate Notion via the Notion MCP, and return the same output format the skill specifies (the brief for `start`, the `+ Suggestion: ... -> url` line for `suggest`, etc.). All task/result links must be formatted as CommonMark markdown links — `[title](url)` — never HTML `<a>` tags and never a bare URL. Claude Code renders markdown but not HTML, so HTML anchors show up as literal text. If the command is `start`, also emit the full kickoff brief verbatim. If anything fails (sync, MCP call, ID resolution), stop and report — do not guess.\n\nYOU MUST ALWAYS PRODUCE OUTPUT. Never return silently. On success: the skill's standard output. On failure: one paragraph describing exactly what failed, what was attempted, and what state Notion was left in. Returning nothing is not an option."
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
   Corpus: [-> <corpus>](<corpus-url>)
   General guidance: [-> Guidance](<guidance-url>)
   Parent: [-> <parent-title>](<parent-url>)   <- only for subtasks
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

## Command: `init [--harness=...] [--haiku=...] [--sonnet=...] [--opus=...]`

**Non-Claude harnesses only.** Configure which models to use for task execution. Claude Code harnesses ignore this; they have built-in model selectors.

**Why it matters:** Cursor, Cline, Continue, and generic MCP harnesses can't spawn subagents with different models on the fly. Instead, store your preferred models upfront in `.claude/skills/agency-os/config.json`, then the skill uses them during batch execution.

**Interactive mode** (recommended):
```
/agency-os init
```

Prompts:
1. Which harness are you using? (or auto-detect from environment)
2. For *easy* mechanical tasks (form fills, recurring routines), which model? (default: haiku-4-5)
3. For *medium* substantive work (drafting, audits, revisions), which model? (default: sonnet-4-6)
4. For *hard* strategic work (design, multi-skill reasoning), which model? (default: opus-4-7)

Stores in `.claude/skills/agency-os/config.json` and prints `config: created -> <path>`.

**Non-interactive mode:**
```
/agency-os init --harness cursor --haiku claude-haiku-4-5 --sonnet claude-sonnet-4-6 --opus claude-opus-4-7
```

If a harness doesn't support a model (e.g., Cursor is configured for only Sonnet), pass the model it does support for all three tiers; the skill will use it for everything.

If `config.json` already exists, re-running `init` overwrites it. To reset: `/agency-os init` interactively.

---

## Command: `scaffold [--parent=<id-or-url>] [--corpora="<n1>,<n2>,..."]`

**The single-shot setup command.** Builds the entire Notion workspace from scratch — Hub page, Tasks database with the full schema below, General Guidance page, Resources page, default corpus pages (`General`, `Recurring`), and every linked DB view. There is no public Notion template to duplicate; this command IS the setup. The integration only needs to be shared with the parent (workspace root or `--parent` page) before running.

Idempotent: if `notion-pointers.json` exists and every ID resolves via `notion-fetch`, prints `scaffold: already in place` and exits. Otherwise creates only what's missing.

1. **Locate or create the Hub**. If `--parent=<page-id-or-url>` is passed, create the Hub as a child of that page (use this when the integration is shared with a specific page rather than the workspace root). Otherwise: search by title at workspace root; create there if absent. If the create fails because the integration lacks workspace-root access, abort with `scaffold: integration must be shared with the workspace root, or pass --parent=<page-id>`.
2. **Create the Tasks database** as a child of the Hub, with the schema above. Capture both `database_id` and `data_source_id`. The `Dependencies` property is a self-relation on Tasks (separate from `Parent Task` — that's the hierarchy relation; `Dependencies` is the gating relation used only by `run`).
3. **Create the General Guidance page** under the Hub; seed body from `references/general-guidance.md`.
4. **Create each Corpus page** under the Hub. Default set: `General`, `Recurring` (user can customise via `--corpora` flag or add later with `add-corpus`). Seed each from `references/corpus-template.md`.
5. **Create the Resources page** under the Hub; seed from `references/resources.md` if present.
6. **Add linked DB views** to the Hub for Suggestions Inbox, In Discussion, To-Do, Recurring, In Progress, Recently Done. Add a per-corpus filtered view to each Corpus page. Every view's SHOW clause must include `Task ID` as the leftmost column so subtask IDs are reachable at a glance.
7. **Wire interlinks** (Hub <-> Guidance <-> Corpora <-> Resources).
8. **Write `notion-pointers.json`**.
9. **Full-width pages — manual one-time toggle.** The Notion MCP doesn't expose `page_full_width`, so Hub / Guidance / Resources / each Corpus page / new task pages need the ... menu -> "Full width" toggle flipped on by the operator after creation. Surface this in scaffold's final output so the operator knows to do it.
10. **Sub-items — manual one-time toggle.** The Notion MCP doesn't expose the Sub-items setting either. On the Tasks DB, the operator must enable Sub-items and wire it to the existing `Parent Task` (parent) / `Subtasks` (children) relation. Path varies by Notion version: typically `...` menu -> "Sub-items" -> pick `Parent Task`. Once wired, every view in the Hub gets a chevron on rows with children.
11. **Print** the Hub URL.

`add-corpus "<name>"` extends the General Plan post-scaffold: appends a `Corpus` select option, creates the page, adds the filtered view, updates pointers. Print: `+ Corpus: [<name>](<url>)`.

---

## Command: `suggest "<title>" ...`

Add a row in `Suggestion` status.

1. Sync preflight.
2. Validate: `--corpus` is in pointers (else list and refuse); if `--type=recurring`, `--cadence` is required.
3. **Dedup check**: refuse if Title-Jaccard >= 0.8 against any row with status in `{Suggestion, Discussion, To-Do, In Progress}`.
4. `notion-create-pages` with parent = Tasks data source. Properties: Title, Status=Suggestion, Corpus, Type, Cadence (if recurring), Effort. Page body = `task-page-template.md` rendered.
5. If `--notes` provided, write into the Description section.
6. Print: `+ Suggestion: [<title>](<url>)`.

---

## Command: `discuss <id>`

Begin clarification on a Suggestion. Flips status to Discussion and prepares the agent to ask clarifying questions.

1. Sync preflight.
2. Resolve `<id>` (UUID, URL, or unique Title substring against `Suggestion` rows).
3. `notion-update-page` Status -> Discussion.
4. **Print the discussion brief**: row properties + Description section. End with: `Ready to clarify. Ask your questions or paste new requirements; the skill will log them with /agency-os log <id> and create subtasks with /agency-os add-subtask <id>. [Open task](<task-url>)`
5. The agent in this conversation now drives the clarification: it asks questions, accepts user answers, calls `log` for each round, calls `add-subtask` whenever the user's responses imply concrete new work.

`discuss` does not require status to be `Suggestion` — calling it on an already-Discussion row is fine and reloads the brief.

---

## Command: `log <id> "<entry>"`

Append a discussion entry to the task page.

1. Sync preflight.
2. Resolve `<id>`.
3. Find or create the `Discussion log` toggle on the page. Append a new dated entry:
   ```
   ### <YYYY-MM-DD> — <auto-summary first 6 words of entry>
   <entry>
   ```
4. Print: `+ Logged: [<title>](<url>)`.
5. If the entry contains lines starting with `+` they're treated as proposed subtasks and surfaced in the output: `note: detected N proposed subtasks; create with /agency-os add-subtask <id> "<title>"`.

The agent should call `log` multiple times during a discussion — once per Q/A round, or once per cohesive thought — rather than dumping a single megalogue at the end. This keeps the log queryable by date.

---

## Command: `add-subtask <parent-id> "<title>" ...`

Create a subtask row.

1. Sync preflight.
2. Resolve `<parent-id>`. Refuse if parent's status is `Done` or `Killed`.
3. `notion-create-pages` with parent = Tasks data source. Properties: Title, Status = parent's status (`Discussion` or `To-Do` typically), Corpus = parent's corpus, Parent Task = parent, Type = `one-time`, Effort from flag or default, Dependencies from `--deps` if provided (each id resolved live via Notion; refuse if any id is unknown).
4. Append a line to the parent's Discussion log section: `### <date> — subtask added: [<title>](<url>)`.
5. Print: `+ Subtask of <parent-title>: [<title>](<url>){  deps=N}`.

Subtasks can have their own subtasks (nesting allowed; the skill doesn't enforce a depth limit but warns at depth >= 3).

---

## Structuring work — parent vs subtask vs log entry

The hardest part of using this board well is deciding **what shape** a piece of work takes. Three rules:

**1. A task is a coherent unit with a clear "done" state.** It can be shipped, merged, published, decided. "Set up X integration" is a task. "Think about X" is not.

**2. A subtask is a child task that can be completed independently and is bounded by a deliverable, not by a step.** "Write the onboarding blurb" is a subtask because the blurb is a separable artifact with its own done. "Click submit on the form" is not a subtask — log it in the discussion or done note instead.

Rule of thumb: if you'd naturally hand it to a different agent on a different day, it's a subtask. If you'd do it inline while working the parent, it's a step.

**3. A log entry is a decision, clarification, or update on existing scope.** "Decided to launch Tue not Wed" is a log entry. "Operator handles the review thread" is a log entry, not a subtask.

### Depth

- Top-level: standalone work or a top-level container.
- Subtask (depth 1): the normal case. Most subtasks live here.
- Nested subtask (depth 2): legitimate when a parent has multiple major deliverables, each with its own breakdown.
- Depth 3+: the skill warns. Almost always means the hierarchy should be flattened or split into separate top-level tasks.

### The "move this chat to Notion" workflow

When the user says "save this to Notion", "make this a task", "track this in Notion", "capture this conversation" mid-chat, read the conversation as a **tree, not a transcript**:

1. **Identify the parent task.** -> `/agency-os suggest "<title>" --corpus=<inferred>`.
2. **Open it for discussion immediately.** -> `/agency-os discuss <id>`.
3. **Log the rationale and major decisions** as one or two distilled entries. -> `/agency-os log <id> "<distilled>"`.
4. **Carve out subtasks** for each separable deliverable. -> `/agency-os add-subtask <id> "<title>"` per item.
5. **Stop and ask before approving.** End with: `Captured to <url> in Discussion. Approve when you're ready to schedule.`

---

## Command: `approve <id>`

Promote a task from Discussion -> To-Do, cascading active children.

1. Sync preflight.
2. Resolve `<id>`. Verify status is `Discussion` (or `Suggestion` — fast-track allowed). Refuse otherwise.
3. **Cascade**: collect every descendant with status in `{Suggestion, Discussion}`. For each, set Status -> To-Do.
4. Set the parent's Status -> To-Do. If `--priority` provided, set on the parent only.
5. Append a `### <date> — approved` entry to the parent's Discussion log.
6. Print: `-> To-Do: [<title>](<url>)  (cascaded N subtasks)`.

---

## Command: `start <id>` (alias: `launch`)

Move To-Do -> In Progress and emit the kickoff brief.

1. Sync preflight.
2. Resolve `<id>` (UUID, URL, or substring against To-Do rows).
3. Verify status is `To-Do`. If `Suggestion` -> refuse with `discuss it first`. If `Discussion` -> refuse with `approve it first`. If `In Progress` -> soft-allow (re-emits brief).
4. `notion-update-page` Status -> In Progress.
5. **Assemble the kickoff brief, in this exact order:**

   ```
   ## Task
   [<title>](<notion-url>)  [<corpus> / <priority> / type=<type>{ cadence=<cadence>}{ last_done=<date>} / effort=<effort>]

   ## Description
   <Description toggle body>

   ## Subtasks (N)
   - [Status]  <subtask title>  ->  /agency-os start <subtask-id>
   - ...

   ## Latest discussion entry  (of <K> total)
   <most-recent entry verbatim>
   (For older entries: /agency-os show <id> --section discussion --entry <date>)

   ## Corpus: <name>
   <Goal + Local guidance from the corpus page>

   ## General guidance
   <full general guidance page body>
   ```

6. End with: `Brief loaded. Proceed.`

**Overfeed protection.** The brief never embeds:
- Older discussion entries (only the latest; the rest are referenced by date)
- Sibling tasks
- Subtask bodies (only their titles + status)
- The Done log

---

## Command: `refresh`

Auto-enumerate the agent-runnable To-Do set and write it to `state/todo-ids.json`. **No arguments.** The operator's only job upstream is to mark rows in Notion with `Exec=Agent`; `refresh` then fetches them via the Notion REST API and the sidecar is the enumeration substrate for `run`.

The currently installed Notion MCP does not expose property-filtered enumeration of a data source, so this command shells out to `scripts/query-tasks.py`, which posts to `POST /v1/data_sources/{id}/query` with a server-side `Status="To-Do" AND Exec="Agent"` filter (Notion API version `2025-09-03`). The integration token (`NOTION_KEY` in `.env`) must be shared with the Tasks database.

Run:

```
python .claude/skills/agency-os/scripts/query-tasks.py
```

The script:

1. Loads `NOTION_KEY` from `.env` and `tasks_database.data_source_id` from `references/notion-pointers.json`.
2. Queries the data source with the two-gate filter, paginating through `has_more`/`next_cursor`.
3. For each result, fetches the page's block children once to extract a `description_preview` (the text between the `Description` H2 and the next H2; first 200 chars).
4. Writes `.claude/skills/agency-os/state/todo-ids.json`:
   ```json
   {
     "refreshed_at": "<iso>",
     "tasks": [
       {
         "id": "<uuid>",
         "url": "https://www.notion.so/...",
         "title": "...",
         "corpus": "General",
         "priority": "3",
         "effort": "M",
         "type": "one-time",
         "cadence": null,
         "last_done": null,
         "exec": "Agent",
         "parent_task_id": null,
         "has_todo_subtasks": false,
         "description_preview": "<first 200 chars of Description>",
         "dependencies": [
           { "id": "<uuid>", "status": "Done" },
           { "id": "<uuid>", "status": "To-Do" }
         ]
       }
     ]
   }
   ```
5. Prints a summary: `refreshed: <N> agent-runnable To-Do tasks -> state/todo-ids.json` followed by one line per task.

**Failure modes.** The script aborts with a non-zero exit and an explanatory message if `NOTION_KEY` is missing, the integration is not shared with the database, or the API returns an error. The existing sidecar is overwritten only after the query succeeds end-to-end.

---

## Command: `run [--go]`

Batch-execute every task in `state/todo-ids.json` (which only contains rows with `Status == "To-Do"` AND `Exec == "Agent"`).

**Claude Code:** The Haiku subagent builds the plan from the sidecar; the orchestrator picks a model per task at runtime and spawns execution agents.

**Non-Claude harnesses:** The skill reads `config.json` to determine available models. If `config.json` doesn't exist, run `/agency-os init` first.

**Auto-refresh.** `run` always calls `refresh` as its first step. If `refresh` fails, `run` aborts.

### Plan phase (Haiku subagent)

1. **Execute `scripts/query-tasks.py` via Bash** — this is mandatory and must happen before reading anything. Run `python .claude/skills/agency-os/scripts/query-tasks.py` and verify it exits 0. Only then read the freshly written `state/todo-ids.json`. Never read the sidecar without running the script first; the file on disk is always stale.
2. **Dedup containers.** For each row with `has_todo_subtasks: true`, skip the parent — its work IS its subtasks.
3. **Resolve dependencies.** Each sidecar row carries `dependencies: [{id, status}]`. For every dep:
   - `status == "Done"` -> satisfied, ignore.
   - dep `id` is in the current in-batch set -> record as an **intra-batch** edge.
   - otherwise -> **external blocker**: drop from dispatch plan, collect into `blocked_deps[]`.
4. **Topological stage assignment.** Build a DAG from intra-batch edges; assign each task a stage = `1 + max(stage of its in-batch deps)` (stage 1 = no in-batch deps). If a cycle is detected, abort.
5. Sort within each stage: Priority asc, then overdue-recurring first, then Effort asc.
6. Return the plan to the orchestrator as `stages: [[(id, title, corpus, effort, parent_id, description_preview), ...], ...]` plus `blocked_deps`.

### Dispatch phase (orchestrator)

**Before spawning any execution agent**, the orchestrator prints the plan outline (see `### Output` below) so the user sees which tasks are about to fire, in which stages, with which model per task. Then `dispatching stage 1...` and dispatch begins.

Stages run **sequentially**: every task in stage N must finish before stage N+1 starts. Within a stage, tasks fan out in parallel.

If any task in stage N closes as not Done, stage N+1 tasks that depend on it are dropped; added to the run summary's `blocked-deps`. Stage N+1 tasks whose deps all closed Done still run.

**Claude Code:** The orchestrator picks a model and spawns an execution agent per task.

**Non-Claude harnesses:** The skill reads `config.json` to determine which models are available, then suggests a complexity level (easy/med/hard) for each task based on the same heuristic.

Picker heuristic (same on all harnesses):

- **Haiku (easy)** — mechanical, template-driven, single-skill: form filings, recurring routines, log-and-close mutations, anything that's "fill a form / file a PR / post a comment from a known template."
- **Sonnet (medium, default)** — substantive content/comms work, judgment-bearing audits, multi-step drafting, anything that needs a draft + revision pass.
- **Opus (hard)** — strategic design, multi-skill orchestration, hard reasoning. Rare.

Cap concurrency at **5** parallel execution agents **per stage**.

### Execution-agent contract

**Status discipline is non-negotiable.** Every spawned agent MUST leave the row in a terminal-for-this-run state before returning. No exceptions, no "leave it at In Progress for the operator to see":

| Outcome | Final Status | Closer command |
|---|---|---|
| Full completion | `Done` (one-time) / `To-Do` w/ Last Done bumped (recurring) | `/agency-os done <id> --result-link <url> --note "..."` |
| Partial completion | `Discussion` | `/agency-os move <id> --to discussion` + `/agency-os log <id> "partial: <what's left>"` |
| Blocked on operator action | `Discussion` | `/agency-os move <id> --to discussion` + `/agency-os log <id> "blocked-operator: <what operator must do>"` |
| Needs clarification | `Discussion` | `/agency-os move <id> --to discussion` + `/agency-os log <id> "needs-clarification: <question>"` |
| Failed (crash, tool error, dead-end) | `Discussion` | `/agency-os move <id> --to discussion` + `/agency-os log <id> "failed: <what broke>"` |

Rationale: leaving a row at `In Progress` after the agent has stopped working is a lie about live state. The dashboard ends up cluttered with rows nothing is actually working on, and the next `run` can't tell whether to retry. `Discussion` is the correct holding pen for "an agent looked at this and could not close it" — the operator sees a real queue of things needing attention, and a follow-up `/agency-os approve <id>` is the explicit "try again" signal.

Every spawned agent:

1. Calls `/agency-os start <id>` to load the kickoff brief AND flip the row To-Do -> In Progress. This MUST be the first call; if the row is already In Progress (re-dispatch), `start` is idempotent and re-emits the brief.
2. **Runnability check:** can this task plausibly be completed end-to-end by an agent, or does it require operator action (logging into a personal account, solving a captcha, clicking publish in a UI without API access)?
   - If operator-only: call `/agency-os log <id> "blocked-operator: <one-line what the operator must do>"`, then `/agency-os move <id> --to discussion`, then emit the result report (step 6) with `status: blocked-operator`. Do not skip the status flip.
3. Otherwise: execute the brief end-to-end.
4. **Self-assessment.** Before closing: did I complete 100% of the acceptance criteria? Partial completions are **not** Done.
5. **Auto-close — required, every outcome.** Pick the closer command from the table above and run it BEFORE emitting the result report. Verify the closer returned success. If the closer itself errors (e.g. Notion API hiccup), retry once; if it still fails, surface that in the result report's `summary` line as `status: failed` with the closer error appended — but still emit the report.
6. **Result report — required, every run, no exceptions.** The agent's final chat output MUST be a single block in this exact format. Returning nothing is not allowed — not on success, not on failure, not on a crash mid-execution. If the agent hit an unrecoverable error before it could do anything meaningful, it still emits the block with `status: failed` and describes what happened. The `status:` line in the report must agree with the final Notion status: `done` <-> Done, every other status <-> Discussion.

   ```
   ### <task-id> — [<title>](<notion-url>)
   status:       done | blocked-operator | needs-clarification | failed
   model:        haiku | sonnet | opus
   result-link:  <url or ->
   summary:      <1-2 sentences: what was done, or what blocked it>
   next-step:    <only if status != done; what operator should do next>

   #### Full output
   <verbatim full output of the agent's execution — every step taken, every tool result summary, every decision made. Do not truncate. If the agent produced no meaningful output beyond the header fields above, write "(no output)" here.>
   ```

**Orchestrator accountability.** After each stage, the orchestrator must confirm it received a result block from every agent it spawned. If an agent returned empty output or no output:
- Treat it as `status: failed`, `summary: agent returned no output`, `full output: (agent returned no output)`.
- Include it in the run summary under ❌ failed with that note.
- Never omit a task from the summary because its agent was silent.

### Parent-cascade rule

When a **subtask** transitions To-Do -> In Progress (via `start`), the skill also flips its parent To-Do -> In Progress, if the parent is currently `To-Do`. The parent stays In Progress until the operator (or a deliberate later `/agency-os done <parent-id>`) closes it.

### Output

**The plan outline is ALWAYS printed first** — both in dry-run (without `--go`) and in real dispatch (with `--go`). The user must see what's about to fire before any agent spawns. In `--go` mode, after printing the outline, immediately proceed to dispatch — do not pause for confirmation (the `--go` flag already is the confirmation).

Emit the outline as plain markdown (no fenced code block, so the links are clickable):

**plan (`<N>` tasks, `<S>` stages):**

- **stage 1** (`<K>` tasks, parallel):
  - `[haiku]` [title](url)
  - `[sonnet]` [title](url)
  - ...
- **stage 2** (`<L>` tasks, parallel, after stage 1):
  - `[haiku]` [title](url) — deps: [dep-title](dep-url)
  - ...

If any tasks were dropped for external blockers, follow with:

**blocked-deps (`<B>` tasks, not dispatched):**
- [title](url) — missing: [dep-title](dep-url) (or raw dep-id if unknown)

If `blocked-deps` is non-empty, also print: `note: <B> task(s) have dependencies outside this batch. Approve the missing deps or run them first, then /agency-os run again.`

In dry-run mode, the outline IS the entire output — stop here, fire nothing.

In `--go` mode, after the outline, print a one-line marker — `dispatching stage 1...` — then begin dispatch. After completion, the orchestrator emits two more sections:

**1. Per-task detail** — one block per task executed, in stage order, verbatim from each execution agent's result report:

```
---
### <task-id> — [<title>](<notion-url>)
status:       done | blocked-operator | needs-clarification | failed
model:        haiku | sonnet | opus
result-link:  <url or ->
summary:      <...>
next-step:    <...>

#### Full output
<verbatim agent output>
---
```

**2. Run summary** — after all per-task blocks. **Do NOT wrap the summary in a fenced code block** (```), because markdown links inside code fences render as literal text in Claude Code. Emit the summary as plain markdown so `[title](url)` links are clickable:

**run summary (T queued, S stages):**
- ✅ done (`<N>`): [title](url), [title](url), ...
- 🟡 needs operator (`<M>`): [title](url), ...
- 🟡 needs clarification (`<P>`): [title](url), ...
- 🟡 blocked-deps (`<B>`): [title](url) (dep: [dep-title](dep-url)), ...
- ❌ failed (`<Q>`): [title](url), ...

Omit any row whose count is 0.

`blocked-deps` entries also surface which dep blocked them. The orchestrator must emit both sections — the per-task detail AND the summary — every time `--go` is used.

---

## Command: `done <id>`

Close a task. Branches on `Type`.

1. Sync preflight.
2. Resolve `<id>` against rows in `In Progress` (preferred) or `To-Do` (allowed).
3. **If `Type == "one-time"`:**
   - Status -> Done; Done At -> today; Result Link -> `--result-link` if given.
   - Append `### <date>: done — <note or "(no note)">` to the Done log.
   - For subtasks: if **all** siblings are now `Done`, surface a nudge: `note: all subtasks of <parent> are done — consider /agency-os done <parent>`.
4. **If `Type == "recurring"`:**
   - Status -> To-Do (loops back).
   - Last Done -> today.
   - Append `### <date>: done — <note>` to the Done log.
5. Print: `✅ Done: [<title>](<result-link>)` (if no result-link, omit the link and print title as plain text).

---

## Command: `kill <id> [--reason "..."]`

Terminal drop.

1. Sync preflight.
2. Resolve `<id>` against any non-terminal row.
3. Status -> Killed. Append `### <date>: killed — <reason>` to the Done log.
4. **Cascade**: for every descendant in non-terminal status, also set Status -> Killed with reason `parent killed`.
5. Print: `✗ Killed: [<title>](<url>)  ({<reason>})  (cascaded N descendants)`.

---

## Command: `next [N] [--corpus=<s>]`

Show top N (default 3) To-Do tasks. **Does not execute.**

1. Sync preflight.
2. Filter: `Status == "To-Do"` and (if `--corpus` given) matching corpus and **`Parent Task IS NULL`** (only top-level).
3. Sort by Priority (1 first; unset last), then Type (recurring with overdue Last Done first), then Created ascending.
4. Print N rows: `<idx>. [<priority>][<corpus>][<type>{<cadence>}][<effort>]  [<title>](<url>)  (/agency-os start <id>)`.

For recurring tasks, "overdue" = `now - Last Done` exceeds the cadence interval (daily=1d, weekly=7d, biweekly=14d, monthly=30d, quarterly=90d, yearly=365d).

---

## Command: `status`

Compact health overview.

1. Sync preflight.
2. Print:
   - Counts per Status.
   - Counts per Corpus x Status (small table).
   - Top 5 Suggestions (most recent).
   - Top 5 To-Do (highest priority + overdue recurring).
   - In Progress rows (flag stale if older than 7 days).
   - Done This Week count.
   - Recurring tasks overdue count.

---

## Command: `list <view> [--corpus=<s>]`

Filtered listing. View in `suggestion | discussion | todo | inprogress | done | killed | recurring | all`.

Output: `[Status][Type][Priority][Corpus]  [<title>](<url>)`.

Subtasks are shown indented under their parent unless `--flat` is passed.

---

## Command: `show <id> [--section ...] [--entry <date>]`

Read a task's content without mutating state. Always include a `[<title>](<url>)` link at the top of the output before showing the requested content.

- Default: row properties + Description + subtask titles.
- `--section description`: Description only.
- `--section discussion [--entry <date>]`: discussion log; one specific entry if `--entry` given.
- `--section donelog`: done log entries.
- `--section all`: everything (full page body + subtask titles).

---

## Command: `update <id> ...`

Mutate properties without changing status. All flags optional. Print: `✓ Updated: [<title>](<url>)`.

`--notes "..."` replaces the Description toggle body. To **append** without replacing, use `log` instead.

`--deps=<id1>,<id2>,...` replaces the Dependencies relation (each id resolved live via Notion; refuse if any is unknown). `--deps=none` clears it. Self-reference and cycles are refused.

---

## Command: `move <id> --to <status>`

Force-set status to any value (escape hatch). Bypasses normal flow gates. Logs a `### <date>: forced move <from> -> <to>` line to the Discussion log. Print: `-> <status>: [<title>](<url>)`.

---

## Natural-language driving

When the user says these things in chat, the skill translates to commands:

| User says | Skill calls |
|---|---|
| "add a suggestion: <title>" / "new idea: <title>" | `suggest "<title>"` (asks for corpus if ambiguous) |
| "let's discuss X" / "open X for discussion" | `discuss <id>` |
| "log: <thing>" / "note that <thing>" (during discuss) | `log <id> "<thing>"` |
| "add a subtask: <title>" / "we'll also need to <thing>" | `add-subtask <parent-id> "<title>"` |
| "approve" / "approve it" / "ship it" / "go ahead" | `approve <id>` |
| "start X" / "launch X" / "let's do X now" | `start <id>` |
| "run todo" / "run all" / "execute the queue" | `run` (dry-run) -> user reviews -> `run --go` |
| "X is done [link <url>]" / "mark X done" | `done <id> [--result-link <url>]` |
| "kill X" / "drop X" / "X is no longer relevant" | `kill <id>` |
| "make X recurring weekly" / "X is recurring monthly" | `update <id> --type=recurring --cadence=weekly` |
| "what's next" / "what should I work on" | `next [N]` |
| "show me X" / "details on X" | `show <id>` |
| "what's the status" / "where are we" | `status` |

**The skill is the user's hands.** When in doubt, the agent asks: "Should I `<command equivalent>` for that?" and only mutates after confirmation. But trivial appends (a `log` entry during an open `discuss` session, an `add-subtask` from an explicit "we'll need to" moment) can be done without asking each time.

---

## Bootstrapping

Fresh workspace — no template duplication required, the command creates everything:

```
/agency-os scaffold
```

If your Notion integration is shared with a specific page rather than the workspace root, pass that page:

```
/agency-os scaffold --parent=<page-id-or-url>
```

You can pass `--corpora "Name1,Name2,Name3"` to scaffold with custom corpus names instead of the defaults (`General`, `Recurring`). You can always add more later with `/agency-os add-corpus "<name>"`.

Migrating from an existing Notion setup:

```
/agency-os scaffold
# then read existing pages, parse content, and:
#   - bulk /agency-os suggest each parsed item with --corpus inferred from heading
#   - copy resource pages to the new Resources page
#   - archive the old structure
# this is a one-shot manual migration; the skill does not provide a generic import command,
# because the source format varies and parsing requires per-source judgment.
```

---

## What this skill does NOT do

- **Does not auto-execute To-Do items.** `next` shows; only `start` (after explicit invocation) loads the brief and flips status.
- **Does not write content, deploy, or run any other skill.** It mutates Notion. The brief may **point** an agent at another skill, but this skill never invokes one.
- **Does not delete content.** `kill` is terminal but archival; the row remains in Notion. To truly remove, archive in Notion manually.
- **Does not commit or push to git** beyond `notion-pointers.json` (which scaffold writes).
- **Does not enforce subtask completion before parent done.** It surfaces a nudge, not a refusal.
- **Does not de-dup beyond Title-Jaccard 0.8 on `suggest`.** Manual rows added via Notion UI bypass the check.
- **Does not auto-archive old discussion entries.** The Discussion log grows unbounded on the page; the brief assembler bounds the agent's context (latest entry only, older ones referenced).
- **Does not run more than one `start` per task at a time.** `In Progress` is the lock.

---

## One-command summary

```
/agency-os suggest -> discuss -> log/add-subtask (clarify) -> approve -> start (loads brief) -> done
                                                                          ^                     |
                                                                          |  (recurring loop)   |
                                                                          +--------------------+
```

Sync runs as preflight. Notion is canonical. The pointer file is the only repo binding. The DB grid stays clean; details fold; briefs stay bounded.
