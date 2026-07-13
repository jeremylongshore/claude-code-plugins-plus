# Agent Comms Mailbox — Protocol

<!-- Copy this file to <comms-dir>/README.md and fill in the handles. -->

Agents working this repo concurrently, with no shared memory or transcript:

- **<HANDLE_A>** — <platform, e.g. Claude Code session>
- **<HANDLE_B>** — <platform, e.g. OpenAI Codex session>

This directory is the only channel between them. Plain Markdown, committed to
the repo — it survives session death and travels with `git pull`. The human
owner audits all channels.

## Files

| File | Written by | Read by |
|---|---|---|
| `<HANDLE_A>.md` | ONLY <HANDLE_A> | everyone else |
| `<HANDLE_B>.md` | ONLY <HANDLE_B> | everyone else |
| `README.md` | either, protocol changes only | all |

**Invariants:** one writer per file; append-only (new entries at the bottom,
never edit or delete past entries); never write another agent's outbox.

## Entry format

```
## [YYYY-MM-DD HH:MM] TYPE: subject
Re: <timestamp+subject of entry being answered, or —>

body — exact paths, file:line, commands, SHAs. Zero-shared-context prose.
```

Types: `STATUS`, `ACTION-REQUESTED`, `QUESTION`, `ANSWER`, `GRILL`,
`EVIDENCE`, `CLAIM`, `RELEASE`, `ACK`.

## Checkpoints

Read every peer outbox at: session start, before starting a new slice, after
completing one. Answer open `ACTION-REQUESTED` / `GRILL` items addressed to
you before starting new work. Write whenever you have verdicts, needs, or
plans affecting shared surfaces, caches, or artifacts.

## Handoffs are grilled

On receiving a handoff, post a `GRILL`: what was verified by running something
(show output) vs. believed; exact file:line of half-applied state; claimed
surfaces; knowledge written down nowhere else; first thing to check if broken.
Answers are `EVIDENCE` entries. Anything unanswerable with evidence is
recorded as a RISK, never dropped. Unanswered grills block `RELEASE`.

## Shared surfaces

`CLAIM` names exact paths before touching a contested surface; `RELEASE` when
done, stating what changed. First claim wins; the other agent posts a
QUESTION or works elsewhere. Never silently overwrite the other agent's work.

## Hygiene

Commit mailbox entries together with the code they describe. Keep entries
concise and factual — the audit trail is the product.
