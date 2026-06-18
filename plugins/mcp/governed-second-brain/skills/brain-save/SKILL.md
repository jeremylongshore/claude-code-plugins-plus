---
name: brain-save
description: |
  Saves a single fact, decision, pattern, or convention into your governed knowledge brain so it can be
  recalled later — and retires memories that are outdated. Side-effecting: it writes to your durable
  corpus, so it never auto-fires — invoke it explicitly. Use when you want the brain to remember
  something specific going forward without a full recompile, or to mark an old memory outdated.
  Trigger with "/brain-save".
allowed-tools: 'mcp__governed-brain__brain_capture, mcp__governed-brain__brain_govern, mcp__governed-brain__brain_transition, mcp__governed-brain__brain_status, mcp__governed-brain__brain_audit_verify'
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: 'Designed for Claude Code; ships with the governed-second-brain plugin. Single-user local — you own the brain. Requires qmd on PATH for the index refresh after govern.'
tags: [brain, governance, save, capture, local-first]
argument-hint: '[save <fact> | retire <memory-id>]'
disable-model-invocation: true
---

# Brain Save — write a fact into your brain (governed)

This is the **write** side of the brain. `/brain` reads; `/brain-save` writes. Use it to tell the brain
to remember a specific fact going forward — without re-running a full compile — or to retire a memory
that's no longer true.

## Overview

The brain learns in two ways: a bulk **compile** ingests a whole corpus at once, and `/brain-save`
adds (or retires) a **single** item on demand. Either way, **governance stays in code**: this skill
*captures* a candidate, then runs the deterministic **govern** step (dedupe → policy → promotion) that
decides what actually gets stored — and writes a SHA-256 hash-chained audit event for the decision. You
are proposing an item for the brain to keep; the deterministic curator owns whether and how it lands.

## Why this never auto-fires

`disable-model-invocation: true` means Claude will not trigger this from conversation — it runs only
when you explicitly type it. Writing to **your durable brain** is a deliberate act, not a chat side
effect. Everything here is **local and single-user**: there is no server, no token, no role — you own
the brain, and the only gate on a write is that you asked for it.

## Prerequisites

- The `governed-second-brain` plugin is installed (it auto-wires the local `governed-brain` MCP server
  with the capture + govern tools).
- `qmd` is on your `PATH` so the govern step can refresh the search index after a promotion. If qmd is
  absent, capture + govern + the audit receipt still complete; only fresh-search visibility waits.

## Instructions

### Save a new fact (capture → govern)

1. Confirm it's worth keeping — *"Would I benefit from finding this in 30 days?"* Skip ephemeral
   debugging steps, throwaway preferences, secrets, or anything already in a CLAUDE.md/README.
2. Pick a category: `decision`, `pattern`, `convention`, `architecture`, `troubleshooting`,
   `onboarding`, or `reference`.
3. Call **`brain_capture`** with `{ title, content, category, filePaths? }`. It appends the candidate to
   the local spool (the model's *proposal*).
4. Call **`brain_govern`** to drain the spool through the deterministic pipeline (dedupe →
   policy/secret-detection → promotion). It returns what was promoted, rejected, flagged, and
   deduplicated, and writes the hash-chained audit event for each decision.

### Retire an outdated memory

1. Find the memory's UUID (via `/brain` search or `brain_status`).
2. Call **`brain_transition`** with `{ memoryId, to, reason, actor }`. Valid moves:
   `active → {deprecated, superseded, archived}`, `deprecated → {active, archived}`,
   `superseded → archived`. Every transition writes a hash-chained audit event.

### Check brain health

Call **`brain_status`** to see counts by lifecycle state and recent rejection feedback before or after
a batch of saves.

### Verify the receipts

Call **`brain_audit_verify`** to check the audit trail's integrity — the SHA-256 hash chain *and* the
external anchor log. It reports any tamper, including a silent rewrite of history that the chain alone
would miss (caught by cross-checking the anchored snapshots that govern commits to git). Use it whenever
you need to prove the record wasn't altered.

## Output

- After a save: report what `brain_govern` returned — promoted vs. rejected vs. duplicate — and that the
  decision was recorded in the audit chain.
- After a retire: report the new lifecycle state and confirm an audit event was written.
- After a status check: summarize counts by lifecycle state and any recent rejections.

## Examples

**Save a decision:**

```
/brain-save I'm going Apache-2.0 across the stack so the public can self-host.

→ brain_capture({ title: "License: Apache-2.0 across the stack",
                  content: "...", category: "decision" })
→ brain_govern()
→ Promoted 1 (qmd://kb-decisions/license-apache-2-0.md); 0 rejected, 0 duplicate.
  Audit event written.
```

**Retire a superseded memory:**

```
/brain-save retire memory 9c2e… — superseded by the new deploy runbook.

→ brain_transition({ memoryId: "9c2e…", to: "archived",
                     reason: "Superseded by the new deploy runbook", actor: "me" })
→ Memory 9c2e… → archived; audit event written.
```

## Error Handling

| Situation                            | Response                                                                                |
| ------------------------------------ | --------------------------------------------------------------------------------------- |
| `brain_govern` rejects the candidate | Policy declined it (e.g. duplicate, too short, possible secret). Report the reason — the governance pipeline working as designed. |
| `qmd` is not on `PATH`               | Govern + audit still complete; the post-promote index refresh is skipped, so the new memory won't show in search until qmd is installed and you re-run govern. |
| `brain_transition` rejects the move  | The lifecycle state machine forbids it; pick a valid target state.                      |
| Content may contain a secret         | Stop and strip it. Do not rely on the pipeline's secret-detection as the only check.    |

## Guardrails

- Never save content containing secrets, tokens, or credentials.
- `reason` on a retire must be a real, human-readable justification — it lands in the permanent audit
  trail.
- A govern rejection is the system working as designed, not a bug to work around.

## Resources

- [Governed Second Brain](https://github.com/intent-solutions-io/governed-second-brain) — the stack and its governance thesis.
- The read counterpart: the `/brain` skill (cited queries).
