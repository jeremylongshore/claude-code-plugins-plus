
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
