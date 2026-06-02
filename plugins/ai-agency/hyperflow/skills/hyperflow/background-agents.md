# Background Agents

Two distinct features both called "background agents" — task-level (this doctrine) and session-level (Claude Code native). They're orthogonal; this section is about hyperflow's task-level pattern.

## Two layers, one name

| Layer | What it is | Surface | Use when |
|---|---|---|---|
| **Task-level** (this doctrine) | Individual worker / observer agents dispatched with `Agent({ ..., run_in_background: true })` within one Claude Code session. Managed via `/hyperflow:background list / show / cancel / prune`. | hyperflow plugin | Latency reduction inside a single chain (Layer 5 gates fired while next batch runs); CI watcher after push; speculative prefetch refreshing `.hyperflow/<analysis>.md` |
| **Session-level** (Claude Code v2.1.139+, May 2026) | An entire Claude Code session runs detached in its own process. Managed via `claude agents` dashboard, launched via `claude --bg`, `/bg`, or `←←` keyboard shortcut. Optional `/goal <condition>` sets an autonomous completion criterion. Idle sessions auto-retire after 5 min. | Claude Code CLI native | Forking a long-running hyperflow chain (`/bg /hyperflow:scope "build user auth"`) so the user keeps the main session free; running multiple parallel features simultaneously across separate background sessions |

They compose: a user can run `/bg /hyperflow:dispatch <slug>` to fire a hyperflow chain in a backgrounded session; inside that session, dispatch can still fire `run_in_background: true` workers for its Layer 5 gates and CI watcher. The two layers cover different scales.

Choose by the unit of work:
- One agent on one task → `run_in_background: true` + `/hyperflow:background`
- Whole interactive session → `/bg` + `claude agents`

Docs: [Claude Code Agent View](https://code.claude.com/docs/en/agent-view) · [Changelog](https://code.claude.com/docs/en/changelog.md).

## Task-level background agents (the rest of this file)

Background agents are dispatched with `run_in_background: true`. The orchestrator does not wait — the chain progresses, and the agent's result is integrated later (or surfaced via notification). Use them for work that does not gate the next decision.

## When to use

Three legitimate patterns:

1. **Latency reduction** — work the chain could await but doesn't need to. Example: Layer 5 quality gates (lint / typecheck / tests) fired after Batch N's PASS while Batch N+1 begins dispatching. Results land before the final integration review.
2. **Observers** — long-running watches of external state the chain can't control. Example: a CI-status watcher fired after `git push` that notifies the user when the remote build completes.
3. **Speculative prefetch** — work that *might* be needed if the chain continues a likely path. Example: scaffold firing a background Searcher to refresh `.hyperflow/architecture.md` while the user is still picking the next skill.

## When NOT to use

Background agents are the wrong tool when:

- The next decision depends on the result. Fire foreground — wait for it.
- The agent would need to call `AskUserQuestion`. Background context cannot interrupt the user — questions belong to the foreground orchestrator.
- The work mutates shared state without coordination (e.g. two background agents both writing to `.hyperflow/memory/learnings.md` race). Serialize through the foreground orchestrator.
- The agent would commit independently. **All commits flow through the foreground per-task / per-batch cadence.** Background results become commit-worthy artefacts at the next user-driven commit, never as standalone background commits (per DOCTRINE rule 9 — no AI-attributed background commits).

## Hard rules (DOCTRINE rule 8 extension)

- **Off by default.** Background dispatch is opt-in per skill via `--background` flag or explicit per-skill config in `~/.hyperflow/config.json`. The orchestrator does not silently fan out background work.
- **No user questions.** A background agent that calls `AskUserQuestion` is a doctrine violation — it interrupts the user from a context they didn't initiate. If the background work surfaces an ambiguity, it surfaces `ESCALATE: background-<purpose> needs user input — chain paused` and the foreground orchestrator decides whether to fire a question.
- **No independent commits.** Background agents may write to `.hyperflow/background/<id>.md` (their output buffer); foreground promotes those results into the next per-task or per-batch commit. Never `git commit` from a background agent.
- **Max runtime cap.** Default 30 minutes (1800s). Configurable per skill via `--background-timeout=<seconds>`. Past the cap, the foreground orchestrator marks the agent as `STALLED` and either retries (max 1 retry) or surfaces ESCALATE.
- **No background-of-background.** A background agent cannot itself spawn background agents — only the foreground orchestrator does. Keeps the agent graph one-deep and traceable.
- **Cancellation on chain abort.** If the user `Ctrl+C` / `Esc` the foreground chain, the orchestrator MUST cancel every in-flight background agent before exit. No orphaned subagents.

## The Background Tasks registry

The foreground orchestrator maintains an in-memory map (also persisted to `.hyperflow/background/registry.json` for `/hyperflow:status` and `/hyperflow:background list`):

```json
{
  "agents": [
    {
      "id": "bg-1718049600-quality-gates-b2",
      "purpose": "Layer 5 quality gates for Batch 2 (lint+typecheck)",
      "fired_at": "2026-05-16T17:30:00Z",
      "timeout_at": "2026-05-16T18:00:00Z",
      "model": "sonnet",
      "status": "running",
      "output_buffer": ".hyperflow/background/bg-1718049600-quality-gates-b2.md",
      "blocks_step": null
    }
  ]
}
```

- `id` — `bg-<unix-ts>-<short-purpose>`
- `blocks_step` — `null` if pure observer / latency; otherwise the upstream step in the foreground chain that must collect this result before advancing (e.g. `dispatch.step3.final-integration` — at the named step, the orchestrator awaits the agent before continuing)

The registry survives session boundaries — on session start, the hook reads it and prints `N background agents in flight (run /hyperflow:background list)` so the user knows what's still running from a prior session.

## Foreground collection points

Background agents that *do* feed back into the chain must declare their `blocks_step` (the chain step that will collect them). At that step, the foreground orchestrator:

1. Checks if the agent is `complete` — collect output buffer.
2. If still `running` — wait up to `min(timeout_at, 2 × foreground-step-deadline)`. Then either collect or mark `STALLED` and ESCALATE.
3. If `error` or `STALLED` — orchestrator decides per skill's error-handling table whether to retry, ESCALATE, or proceed without the result.

Pure observers (`blocks_step: null`) are never awaited — they just emit a `PushNotification` when done, and the user / next session sees the result.

## Result integration

Background agent outputs land in `.hyperflow/background/<id>.md` as a structured block:

```markdown
# Background Result — <purpose>

| Field      | Value                                |
|------------|--------------------------------------|
| Agent ID   | `bg-1718049600-quality-gates-b2`     |
| Fired at   | 2026-05-16T17:30:00Z                 |
| Completed  | 2026-05-16T17:32:18Z (2m 18s)        |
| Status     | complete                             |
| Tokens     | worker 4.2k                          |

## Output

<the agent's structured result — verdict / findings / data, formatted
 per the agent's own contract>
```

The foreground orchestrator either:
- **Integrates** — merges the result into the next foreground artefact (e.g. quality-gate results land in the task file's Verification plan section before final integration review)
- **Surfaces** — if observer-only, prints a one-line status in chat (`Background: CI passed at 17:35 — safe to start the next feature`)
- **Archives** — for results that don't drive further action, leaves the file in `.hyperflow/background/` for inspection via `/hyperflow:background show <id>`

The `.hyperflow/background/` directory is gitignored along with the rest of `.hyperflow/` — these are local working artefacts, not committed history.

## Management commands

`/hyperflow:background list` — show the registry: in-flight, completed-uncollected, stalled, errored.

`/hyperflow:background show <id>` — print one agent's output buffer.

`/hyperflow:background cancel <id>` — cancel a specific in-flight agent.

`/hyperflow:background cancel --all` — cancel every in-flight agent (e.g. before closing a session).

`/hyperflow:background prune` — delete completed `.hyperflow/background/<id>.md` files older than 7 days.

`/hyperflow:status` includes a `Background` section that summarizes the registry (count of running / stalled / completed-uncollected).

## Tier rules (alignment with DOCTRINE Layer 2)

Background agents follow the same tier-routing as foreground:

- **Background workers** (Implementer / Searcher / Writer in latency-reduction or speculative-prefetch patterns) → Sonnet
- **Background observers** (CI watcher, file-change monitor, deploy-status poller) → Sonnet (these are mostly poll loops with simple integration logic, not thinking work)
- **Background Reviewers** — DO NOT EXIST. Reviewers are foreground-only because they gate decisions. If you find yourself reaching for a background Reviewer, you're using the wrong pattern.

## v1 integrations (rolled out separately)

These are the per-skill integrations planned for incremental rollout. Each one ships in its own commit so users can opt in feature-by-feature:

1. **dispatch Step 2b — background quality gates.** Fire lint / typecheck / tests in background after each batch PASS, while Batch N+1 begins dispatching. Collected before Step 3 (final integration review). Latency win on multi-batch chains where gates were the longest serial cost.

2. **deploy Step 7 — background CI watcher.** After `git push`, fire a background agent that polls GitHub Actions / equivalent for build status. Emits notification when the build completes (PASS / FAIL / TIMEOUT). User runs more work in the meantime; if FAIL, the next foreground skill invocation prints a status banner with a link to the failed run.

3. **scaffold — background analysis refresh.** When `.hyperflow/.checksums` shows config files changed since the last refresh, fire a background Searcher to refresh affected `.hyperflow/<analysis>.md` files. Doesn't block session start; results land before the next user-invoked skill.

4. **cache compact — background mode.** Session-start advisory offers a third option beyond "compact now / skip": "compact in background". Fires the Compaction Writer with `run_in_background: true`, returns to the user immediately, notifies on completion.

Each integration is shipped as a `feat(<skill>): background <purpose>` commit with its own opt-in flag / config.

## Failure modes

| Failure | Behavior |
|---|---|
| Background agent times out (past `timeout_at`) | Mark `STALLED`. If `blocks_step` is set, foreground at that step retries once with same args; second timeout → ESCALATE with full registry entry. If pure observer, mark and continue; user sees via `/hyperflow:background list`. |
| Background agent returns `SECURITY_VIOLATION` | Halt the foreground chain at the next foreground step (or immediately if `blocks_step` is set). Treat identically to a foreground SECURITY_VIOLATION. |
| Background agent crashes / errors | Mark `error`. Foreground collection point retries once; second crash → ESCALATE. |
| Two background agents race on the same file | Foreground orchestrator MUST serialize file writes — never dispatch two background agents that target the same `.hyperflow/<x>.md` file. If a use case requires concurrent writers, the foreground step that orchestrates them serializes via a small in-memory lock keyed by file path. |
| Session ends while agents are still running | Registry persists. Next session start prints `N background agents in flight from prior session — running /hyperflow:background list…` and lists their state. User decides whether to wait, cancel, or collect. |
| User runs `/clear` (Claude Code) mid-chain | Same as session end — registry survives, in-flight agents continue in their own contexts until they complete or their session-level runtime decides otherwise (provider-specific). |
| Background agent tries `AskUserQuestion` | Hard failure — log to `.hyperflow/background/<id>.md` with `status: doctrine-violation` and surface ESCALATE on next foreground collection. |
| Background agent tries to `git commit` | Same — hard failure with `status: doctrine-violation`. |

## Anti-patterns

- **Background AskUserQuestion** — questions belong to the foreground orchestrator
- **Background commits** — all commits flow through foreground cadence
- **Background Reviewers** — reviewers gate decisions; backgrounding them defeats the gate
- **Background-of-background** — fan-out depth stays at one
- **Forgetting to cancel on abort** — orphaned subagents waste tokens after the user stops the chain
- **Background work that the foreground silently ignores** — every background dispatch must have a clear collection point (or be a documented observer with a notification path)
- **Treating background as "free"** — background agents cost tokens. Each one fired counts in the chain's total budget. The decision to background is about latency, not cost.
