# Escalation and token accounting

## Why mid-flight changes happen

Triage is a forecast, not a contract. The orchestrator picks a flow profile based on the task description before any real work begins — but workers encounter ground truth: the actual files, the real dependencies, the production blast radius. A "fast" one-liner can turn out to call a shared utility touched in eight places; a "deep" refactor can resolve to a two-line patch after research. Escalation lets the flow adapt to reality without discarding completed work or restarting from scratch. The worker's partial output is always preserved as context for the next batch.

The two axes of mid-flight change are independent:

- **Complexity escalation** — scope is larger than triage predicted. More files, more subsystems, more coordination needed. The response is to move to a heavier profile.
- **Risk escalation** — consequences are more severe than triage predicted. The change now touches prod config, auth, or irreversible data. The response is always a hard stop and user confirmation, regardless of profile.

Either axis can trigger independently. A trivial one-line change can trigger risk escalation (if it touches secrets). A massive cross-cutting refactor may never trigger risk escalation (if every change is fully reversible). Treat them separately.

---

## The ESCALATE signal

Workers — especially implementers and searchers — return a special prefix when they hit unexpected complexity that exceeds what their current profile was designed to handle:

```text
ESCALATE: <reason>

<rest of normal worker output — what they DID find/do before stopping>
```

The reason must be a concrete one-liner. The output below it must describe work already completed so the orchestrator can build on it.

Example of a well-formed ESCALATE response:

```text
ESCALATE: discovered cross-cutting impact — the `userService.ts` change ripples into
6 controller files and a shared middleware layer that wasn't in scope.

Before stopping, I completed:
- Located the primary change site in `src/services/userService.ts` (line 142)
- Verified the function signature change is backward-compatible in isolation
- Identified 6 downstream callers: authController, profileController, adminController,
  sessionMiddleware, auditLogger, and the userRepository test suite

The callers need review before this change can safely land. I did not modify any files.
```

This format gives the orchestrator everything it needs: the reason for escalation, what is already known, and a clean stopping point.

**Reasons that trigger ESCALATE:**

- "discovered cross-cutting impact in 6 files, not the 2 I was given"
- "this requires a database migration that wasn't in scope"
- "the existing code doesn't match the assumed pattern; need an architectural decision"
- "this code is calling a third-party API I don't have credentials for — need design input"
- "I found a security vulnerability in the surrounding code that affects this change"
- "this requires changes to a config file that affects prod deployment"
- "scope-expansion: change touches auth layer unexpectedly"

**Reasons that do NOT trigger ESCALATE (worker should solve them locally):**

- "I needed to add an import"
- "the existing code has a minor formatting issue"
- "I made a different naming choice than suggested"
- "the file was split across two modules instead of one"

---

## The DOWNGRADE signal

Downgrade is the orchestrator's own decision, not a worker signal. Workers never return a downgrade signal — they complete their work or escalate. The orchestrator alone decides to downgrade, based on what the research or brainstorm phase revealed. When the orchestrator determines the original profile is overkill, it emits:

```text
⬇ DOWNGRADED: <from> → <to>. Reason: <reason>
```

Downgrade never requires user confirmation unless the user explicitly locked the profile at session start (e.g., "use deep profile, I want full review"). Downgrade is always optional — the orchestrator should err toward keeping the higher profile when uncertain. The savings from a downgrade are real but secondary to getting the task right.

Downgrade decisions are made at natural batch boundaries, not mid-batch. The orchestrator completes the current batch at the original profile, then re-evaluates before dispatching the next.

---

## Profile budget reference

Each profile's baseline token budget is defined in `model-config.md`. For escalation decisions, use these approximate values:

| Profile | Baseline budget |
|---|---|
| fast | 30k tokens |
| standard | 100k tokens |
| deep | 300k tokens |
| scientific | 300k tokens |
| research | 80k tokens |
| creative | 150k tokens |

Source of truth: `flow-profiles.md` — values must match.

These are the denominators used when computing the overrun multiplier. If `model-config.md` defines a different value, that value takes precedence over this table.

---

## Escalation paths

| From profile | Trigger | To profile | Why |
|---|---|---|---|
| fast | scope larger than single-file | standard | needs reviewer + task file |
| fast | cross-cutting concern surfaced | deep | needs full decomposition |
| fast | risk became irreversible | standard or deep | needs explicit approval gate |
| standard | cross-cutting impact across 5+ files | deep | needs full pipeline |
| standard | security vulnerability discovered | deep + security focus | needs L1–L5 review |
| standard | scope expanded beyond initial files | deep | decomposition required |
| research | implementation needed after evaluation | standard or deep | flip from read-only to write |
| creative | implementation requires cross-cutting infra changes | deep | cross-cutting needs full pipeline |
| creative | security or scientific concerns emerge during design | deep + (security or scientific) focus | additional rigor needed |
| creative | scope exceeds 5 files | deep | decomposition needed |
| any | numerical or proof correctness emerged | scientific | TDD required |
| any | irreversible action requested by code | halt → user approval | irreversibility always requires consent |

---

## Downgrade paths

| From profile | Observation | To profile | Why |
|---|---|---|---|
| deep | research showed only 1–2 files affected | standard | save tokens, reduce overhead |
| deep | brainstorm converged fast, no cross-cutting | standard | full pipeline is overkill |
| standard | turned out to be a one-line fix after research | fast | optional — only if risk is clearly reversible |
| scientific | tests already exist and only docs changed | standard | full TDD cycle is overkill |
| creative | trivial design tweak (e.g. color change, copy edit) | fast or standard | full creative pipeline overkill |

---

## Escalation flow

When a worker returns `ESCALATE: <reason>`, the orchestrator follows this sequence:

1. Pause dispatch of any pending workers in the current batch immediately. Workers already running in parallel may finish, but do not start new ones.
2. Read the worker's full output — extract what was completed before the escalation point and what the specific blocker is.
3. Update the in-memory triage record with the new information: affected files, risk surface, actual scope, any new types discovered (e.g., `db` was not in the original triage but a migration is now needed).
4. Pick the new profile per the escalation paths table above. If multiple paths apply, take the highest profile.
5. Print to the user:
   ```text
   ESCALATED — <from> → <to> · reason: <reason>
   ```
6. Preserve the worker's partial output as input context for the next batch. Prepend it to the next batch's context as: `Prior work (before escalation): <output>`. Do not discard completed work.
7. Re-plan: generate a fresh task breakdown under the new profile. Completed sub-tasks do not need to be re-run unless the escalation reason invalidates them.
8. If the escalation crosses the irreversibility boundary (see Risk escalation below), call `AskUserQuestion` for explicit consent before step 7.
9. Log the escalation event for the usage summary: `from_profile`, `to_profile`, `reason`, `batch_number`, `tokens_at_point`.

Multiple escalations in one session are valid. Each escalation re-evaluates from the current state — a second escalation from `standard → deep` after a first `fast → standard` is normal. Log each independently.

---

## Risk escalation

Complexity escalation is about scope. Risk escalation is about consequences. They can happen independently and each requires a different response.

A task escalates risk when ANY of the following surface mid-flight:

- A change to a config file deployed to production
- A schema migration that drops or renames a column with existing data
- A new external API call to a billable or rate-limited third-party service
- A change to authentication or authorization logic
- A change to secrets handling, key rotation, key storage, or encryption algorithms
- A force-push, branch deletion, or history rewrite
- Any write operation to a production database from application code
- Disabling or weakening a security control (firewall rule, CORS policy, CSP header)

**When risk escalation occurs:**

1. Worker MUST stop immediately. Do not make the change. Return:
   ```text
   ESCALATE: risk-irreversible — <specific details of what was found>

   <description of work completed up to this point>
   ```
2. Orchestrator MUST call `AskUserQuestion` for explicit consent before any further action. The question must include: what the risky action is, what it would affect, and what happens if it goes wrong.
3. Orchestrator prints:
   ```text
   🔴 RISK ESCALATION: irreversible action detected — <details>
   Paused. Awaiting user approval before proceeding.
   ```
4. No automatic fall-through to a deeper profile without the user's explicit yes. The user must say yes to the specific risky action — generic approval of the task is not sufficient.
5. If the user declines, orchestrator marks the task blocked and surfaces a safe partial result with a clear note about what was skipped and why.
6. If the user approves, orchestrator logs the approval (user said yes at `<timestamp>` to `<action>`) and resumes at the appropriate profile.

Risk escalation always supersedes complexity escalation. A "fast" task that discovers a prod config change halts fully — there is no "fast risk escalation." The profile level is irrelevant once irreversibility is detected.

---

## Token accounting protocol

Token accounting is not optional and not approximate. The orchestrator tracks exact token usage from every agent after every dispatch. This data drives the overrun thresholds, feeds the usage summary, and is the audit trail if a user asks why a task consumed more than expected.

The orchestrator tracks token usage from every agent after each dispatch:

```text
agent_id | role      | model       | input_tokens | output_tokens | total_tokens | timestamp
---------|-----------|-------------|--------------|---------------|--------------|----------
t-01     | triage    | opus-4-8    | 1200         | 340           | 1540         | T+0s
w-01     | searcher  | sonnet-4-6  | 3100         | 890           | 3990         | T+12s
w-02     | implementer | sonnet-4-6 | 4200        | 1100          | 5300         | T+12s
r-01     | reviewer  | opus-4-8    | 6800         | 420           | 7220         | T+28s
```

After each batch completes:

1. Sum tokens by role (thinking agents vs. workers vs. reviewers).
2. Compute the running total across all batches so far.
3. Compare against the profile's baseline budget (defined in `model-config.md`).
4. Apply the thresholds in the Budget overrun handling table below.
5. Append the batch summary to the in-memory usage log for the final summary.

Token counts must come from the actual API response metadata, not estimated from prompt length. If a model call does not return token metadata, log a warning and use a conservative estimate of 2× prompt character count ÷ 4.

---

## Budget overrun handling

| Multiplier | Indicator | Behavior |
|---|---|---|
| 1.0× — 1.5× | gray (internal log) | Log to running counter; no user-facing output |
| 1.5× — 2.0× | yellow `⚠ APPROACHING BUDGET` | Print warning to user; suggest downgrade if remaining work is light |
| 2.0×+ | red `⚠ OVER BUDGET` | Halt batch; call `AskUserQuestion` to confirm continuation |

**Exception:** For `scientific` and `deep` profiles where the user explicitly requested thoroughness (e.g., "full audit", "exhaustive review", "I want every edge case covered"), the halt threshold rises to 3.0×. Flag with red at 2.0× anyway, but do not halt until 3.0×.

When `AskUserQuestion` fires on budget overrun, present the following structured choices:

```text
⚠ OVER BUDGET: this task has used <X>k tokens against a <Y>k profile budget (<Z>× over).
Remaining work estimate: ~<N>k tokens if continued at current profile.

How would you like to proceed?
A) Continue at current profile (<Z>× total estimated)
B) Downgrade to <lower-profile> to reduce remaining cost (~<M>k estimated)
C) Stop here — summarize what was completed and what remains
```

The orchestrator must not guess the user's preference and continue. It must pause and wait for a response. If the user does not respond within the session, default to option C (stop and summarize).

---

## Usage summary format

Print this block at the end of every task, regardless of profile. It is always the last thing printed — after the actual task output, not before. The summary is for the user's awareness of cost and process, not a replacement for the task result itself.

```text
── Hyperflow Usage ─────────────────────────────────
Triage:      moderate   · flow: standard   · types: [api, db]
Profile:     standard   · budget: 100k     · actual: 87k  (under)
Spec depth:  light      · 1 question       · 2.3k tokens
─────────────────────────────────────────────────────
Thinking  (Opus 4.8  )   2 agents    42.1k tokens
Worker    (Sonnet 4.6)   3 agents    45.0k tokens
Total                    5 agents    87.1k tokens
─────────────────────────────────────────────────────
Escalations: 0   · Downgrades: 0   · Overruns: none
```

For tasks with escalation, replace the last line with:

```text
Escalations: 1 (fast → standard, reason: scope-expansion)
Downgrades: 0   · Overruns: none
```

For budget overruns:

```text
Escalations: 0   · Downgrades: 0   · Overruns: 1 (1.7× at batch 3, yellow)
```

The `actual` field reads `under`, `over`, `yellow` (1.5×–2.0×), or `red` (>2.0×). No icons or emoji — plain words only.

The `types` field mirrors what triage identified (e.g., `[api, db, config]`). If escalation surfaced new types mid-flight, append them with a `*` marker: `[api, db, config*]` where `*` means discovered during execution.

If the task was downgraded, the profile line reads: `Profile: deep → standard · budget: 200k → 100k · actual: 78k (under)` to make the downgrade visible at a glance.

---

## Anti-patterns

**Do not escalate for solvable local decisions.** Adding an import, renaming a variable, or choosing between two equivalent implementations are not escalation triggers. Workers must exhaust their own judgment first. A worker who escalates on every surprise is noise, not signal.

**Do not downgrade to save tokens if the task is risky.** Token budget is secondary to correctness and safety. Never downgrade a task touching auth, secrets, or prod config just because it is running long. When in doubt: stay at the higher profile.

**Do not swallow ESCALATE signals.** If a worker returns `ESCALATE:`, the orchestrator must surface it. Silent escalation handling (absorbing the signal and continuing at the same profile) defeats the purpose and hides scope creep from the user. The `ESCALATED —` line must always be printed.

**Do not skip risk escalation for "small" irreversible changes.** There is no such thing as a small schema drop or a minor auth bypass. The irreversibility check is binary — it either is or it isn't. Size does not factor in.

**Do not print the usage summary before work is complete.** The summary is a terminal output — it signals to the user that the task is done. Printing it mid-flight creates false closure and confusion about whether the task finished.

**Do not track tokens at task level only.** Token accounting must be per-agent and per-batch so the orchestrator can catch overruns early, not only at the end. A task that goes 2× over budget on batch 1 of 5 should halt then, not after all 5 batches complete.

**Do not re-run completed sub-tasks after escalation unless the escalation reason invalidates them.** If a worker found and documented 3 files correctly before escalating, those 3 files are already known — do not search them again. Escalation adds capacity, it does not reset progress.

**Do not present escalation as failure.** Escalation is the system working correctly. The user should understand it as "the task revealed itself to be larger than initially assessed" — not as an error or a mistake by the orchestrator.
