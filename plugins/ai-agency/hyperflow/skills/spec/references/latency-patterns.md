# Latency patterns (P1–P5 + Round 2 L1-L9)

## Purpose

Five orthogonal latency-reduction patterns (P1–P5, round 1) plus nine additional levers (L1–L9, round 2) applied across `spec`, `scope`, and `dispatch`. Round 1 patterns change *when* and *how* calls fire, not the tier mix. Round 2 patterns reduce call *count* and call *tier* — acknowledging that Opus ceremony around mechanical orchestration steps costs wall-clock without quality return.

## Wall-clock impact

| Pattern | Applies to | Wall-clock win |
|---|---|---|
| P1 — Parallel sibling drafts | spec §7, scope Step 2 (research Searchers) + Step 4 (Writer-internal section parallelism) | ~5x on section work |
| P2 — Batched single-pass review | spec §7, scope, dispatch | ~5x reviewer calls collapsed |
| P3 — Concurrent independent pre-conditions | spec §1+§2, §5+§6, all skills | ~2x on independent steps |
| P4 — Triage-driven step skipping | spec §3, §6 | up to 100% on low-ambiguity |
| P5 — Lean worker prompts via memory references | all skills | ~30% TTFT reduction |

**Median spec run (round 1):** ~16 sequential round-trips before → ~6 after. ~60% wall-clock reduction, zero change to which tier reviews what.

**Dispatch (workhorse, round 1):** P2 alone collapses N per-sub-task Opus reviews into 1 batched review per batch. On a 3-batch task with 4 sub-tasks per batch: 12 reviewer calls → 3. ~75% reviewer-phase latency reduction.

### Round 2 expected outcomes (median chain: single feature, 3 batches, standard complexity)

| Phase | Round 1 | Round 2 | Cut |
|---|---|---|---|
| Spec | 30-45s | 18-28s | ~40% additional |
| Dispatch (per-batch) | 25-40s | 18-28s | ~30% additional |
| Wrap-up | 8-15s | 1-2s (inline) | ~85% |
| End-of-chain gates | 2 round-trips | 1 round-trip | -50% |

**Median chain wall-clock:** round 1 ~90-130s → round 2 ~55-80s. ~35-40% additional reduction on top of round 1's ~50-60%. Cumulative vs pre-round-1 baseline: ~70-75% faster end-to-end.

**Opus call count (median chain):** round 1 5-7 calls → round 2 3-4 calls (drop wrap-up Reviewer, skip integration review when green, drop spec coverage Reviewer).

---

## P1 — Parallel sibling drafts

**What it is:** Draft multiple independent sections simultaneously by dispatching all sibling workers in a single message with parallel `Agent` calls — the same pattern `dispatch` uses for batch workers, applied back to `spec` §7 and `scope` decomposition.

**When siblings qualify:**
- No inter-dependencies (section A's output is not an input to section B)
- All share the same upstream input (e.g., a single approved approach feeds all 5 design sections)
- Sibling count matches the natural structure: 5 spec sections (Architecture, Data flow, Key decisions, Edge cases, File structure); do not artificially split to inflate parallelism

**Dispatch pattern:** Fire all sibling Worker agents in one message. Wait for all to return before advancing to the Reviewer step.

**Example:**

```
[spec §7] approved approach → single message →
  Worker §A (Architecture)    ↘
  Worker §B (Data flow)        → all parallel
  Worker §C (Key decisions)    →
  Worker §D (Edge cases)       →
  Worker §E (File structure)  ↗
→ wait for all 5 → P2 batched review
```

**Why quality is preserved:** The Reviewer still reviews every section. Parallelizing the draft phase does not touch the review phase.

**When to disable:** `--thorough` / `depth=max` flag disables P1 for steps where a prior section's output could meaningfully shape a later section's approach (rare in spec §7, common in narrative prose).

**Scope-specific carve-out (critical):** `--thorough` does NOT disable P1 for scope Step 2's parallel Searchers. Those two Searchers are independent reads — neither's output is an input to the other — so sequencing them provides no quality benefit regardless of flag. `--thorough` only disables P1 where section-order dependency is plausible:
- Step 4 Writer-internal section parallelism (spec §7 and scope's Writer step)
- Anywhere else sibling content could cross-influence

**Scope P1 surface under `--thorough`:**

| Scope step | P1 under default | P1 under `--thorough` |
|---|---|---|
| Step 2 — parallel research Searchers | On | **On** (independent reads, no tradeoff) |
| Step 4 — Writer-internal section parallelism | On | **Off** (serialized for section coherence) |

If in doubt about whether siblings are truly independent, keep P1 on — the Reviewer catches cross-section conflicts.

---

## P2 — Batched single-pass review

**What it is:** After N parallel drafts complete, dispatch **one** Opus Reviewer with all N sections in its prompt instead of N separate reviewer calls.

**When applicable:** N siblings have completed at the same review-level cap (e.g., all are L3 or all are L5). Do not batch siblings that have different level caps — see "When NOT to use" below.

**Per-sibling verdict format** (Reviewer must return one block per section):

```
§1 Architecture:   PASS
§2 Data flow:      NEEDS_FIX — [specific feedback]
§3 Key decisions:  PASS
§4 Edge cases:     PASS
§5 File structure: PASS
```

For each `NEEDS_FIX` section: re-dispatch only that section's Worker; single Opus re-review of just that section. Do not redraft passing siblings.

**Cross-section coherence benefit:** Batched review is strictly better for coherence than sequential per-section review — the Reviewer sees all sections simultaneously and can catch conflicts that per-section passes miss (e.g., a contradiction between §1 Architecture and §5 File structure that neither section alone would reveal).

**Prompt template:** See `skills/hyperflow/reviewer-prompt-batched.md` for the exact prompt structure, verdict format, and NEEDS_FIX handling rules.

**When NOT to use:**
- Siblings have different reviewer-level caps (e.g., some are L3, some require L5 — batch only within the same cap)
- One sibling's content is logically dependent on another sibling's draft completing first (use P1's sequencing to resolve, then batch the independent set)
- The batch would exceed the Reviewer's safe context window — cap at 5 siblings per batch call

**Why quality is preserved:** Thinking-tier reasoning over N sections in one pass is at least as rigorous as N separate passes, and cross-section coherence checking improves.

---

## P3 — Concurrent independent pre-conditions

**What it is:** Dispatch two or more pre-condition steps in the same message when their outputs do not depend on each other.

**Identifying independence:** Step A and Step B are independent if the output of A is not an input to B and the output of B is not an input to A. Both may share an upstream input without losing independence.

**Examples (spec flow):**

| Concurrent pair | Why independent |
|---|---|
| Step 1 Classifier ∥ Step 2 Searcher | Searcher maps existing context; does not need triage output to begin |
| Step 5 Synthesis Writer ∥ Step 6 Approaches Writer | Both depend on Step 4 answers, but neither depends on the other's output |

**Dispatch pattern:** Fire both in one message; wait for both before advancing to the dependent step.

**Race-case handling:** If one step fails or returns thin output before the other completes:
- Allow the other to complete
- Reviewer at the next step redispatches the thin result with a better-scoped query informed by the companion output
- Do not re-run both — only the incomplete one

**P3 stays on always.** The `--thorough` flag does not disable P3 — there is no quality tradeoff in running truly independent steps concurrently. Never introduce artificial sequencing between independent steps to appear more thorough.

---

## P4 — Triage-driven step skipping

**What it is:** Skip spec ceremony steps that add no value when the request is already clear and unambiguous.

**Thresholds (round 2 — updated by D8/L8):**

| Condition | Steps skipped | Rationale |
|---|---|---|
| `ambiguity < 0.6 AND complexity != high` | Step 3 (6-dim analysis) + Step 6 (2–3 approach proposals) | Nothing ambiguous to analyze; one clear approach exists |
| `ambiguity < 0.4 AND complexity == low` | Entire spec skill | Bounce directly to `scope` — spec ceremony adds no value |

**Steps always kept regardless of triage:**
- Step 7 sections (the design walk-through is the deliverable)
- Step 4 questions (2-question floor is a structural gate per DOCTRINE rule 8)

**Borderline rounding rule:** When `ambiguity` lands at or near the threshold (e.g., 0.39, 0.41), **round up** — run the optional steps. The latency win matters on the clearly unambiguous cases; borderline cases keep the full ceremony. Never skip on the fence.

**How this is enforced:** The skill reads `triage.ambiguity` and `triage.complexity` from the triage JSON (see `task-triage.md`) at Step 0, before any step dispatch. Gate logic executes inline in the orchestrator, not inside a Worker.

**When to disable:** `--thorough` / `depth=max` flag disables P4. All steps run regardless of triage scores.

---

## P5 — Lean worker prompts via memory references

**What it is:** Replace inlined context blocks in worker prompts with a 200-token pointer to `.hyperflow/memory/`, letting workers `Read` only what they need rather than receiving everything upfront.

**Why TTFT matters:** Time-to-first-token at the API layer grows with prompt size. Smaller prompts = faster first token = lower wall-clock latency per call, multiplied across every worker in a batch. Token cost is a side benefit; wall-clock is the goal.

**Pointer pattern (replaces inlined blocks):**

```
You have access to project context — read these files as needed:

.hyperflow/ root (project analysis from scaffold Step 1):
  - profile.md        — project conventions
  - architecture.md   — system architecture
  - conventions.md    — naming, patterns, standards

.hyperflow/memory/ (orchestration + accumulated state from scaffold Step 2):
  - doctrine.md       — orchestration rules (read once if unfamiliar)
  - learnings.md      — accumulated lessons from prior batches in this run
  - decisions.md, pitfalls.md, patterns.md — memory stubs

Your task: <inline task description here>
```

Workers `Read` only the files relevant to their task. Doctrine is read once per session by the first worker that needs it, not re-inlined on every dispatch.

**Prompt template:** See `skills/hyperflow/worker-prompt-lean.md` for the full lean-prompt template — that file is the canonical source. This block is illustrative only.

**Fallback for absent or stub files:** If a referenced file is absent OR appears to be an unpopulated stub (matches a `<!-- to be populated -->` sentinel or has fewer than ~5 meaningful body lines), the worker falls back to a brief inline default for THAT file only — not a wholesale switch to the full prompt. Partial population is the expected failure mode (scaffold creates the directory with stubs); a wholly-missing `.hyperflow/` is the rare edge case.

**P5 stays on always.** The `--thorough` flag does not disable P5 — there is no quality tradeoff in lean prompts. Workers still have access to the full context; they fetch it on demand.

---

## Round 2 patterns (L1-L9)

Round 2 reduces call **count** and call **tier**. The doctrine floor `thinking agents ≥ batches + 2` becomes `≥ batches + 1` (L5 drops wrap-up Reviewer), and several Opus reviewers either downshift to Haiku, become conditional, or are dropped when the work they review is mechanical.

---

### L1 — Haiku Classifier (D1)

**What it is:** Triage Classifier (spec Step 1) dispatched at Haiku 4.5 tier instead of Sonnet/Opus.

**When applicable:** Always — triage produces structured JSON (`types[], complexity, risk, ambiguity, flow, personas[]`). Haiku 4.5 handles structured classification at near-Opus quality for this task shape, at ~10x lower latency and ~15x lower cost. Fallback: if Haiku unavailable, fall back to Sonnet.

**`--thorough` behavior:** Does NOT change this lever. Haiku classification is high-quality for the structured JSON output shape; no accuracy tradeoff justifies reverting to a higher tier.

---

### L2 — Combined audit+deploy gate (D2)

**What it is:** Merge the two sequential end-of-chain `AskUserQuestion` calls (audit gate + deploy gate) into a single multi-question call.

**When applicable:** Always at end-of-chain — two sequential user round-trips is pure latency overhead. Branching logic (audit Yes + deploy No → run audit, stop before deploy) is fully preserved.

**`--thorough` behavior:** Does NOT change this lever. No quality tradeoff — questions are identical, branching is identical. The only change is one fewer user round-trip.

---

### L3 — Session-cached context (D3)

**What it is:** `hooks/session-start` concatenates `.hyperflow/profile.md`, `architecture.md`, and `conventions.md` into a single `.hyperflow/memory/session-context.md` bundle at session start. Workers reference the bundle instead of reading three separate files.

**When applicable:** Always when `.hyperflow/` is populated. Mid-session changes to source files do not propagate until next session-start (document the limit). Workers can still `Read` source files directly if they suspect staleness.

**`--thorough` behavior:** Does NOT change this lever. Workers retain full context access; they simply read it from a pre-bundled file rather than three files.

---

### L4 — Drop spec Searcher coverage Reviewer (D4)

**What it is:** Remove the Opus Reviewer that reviewed the spec Step 2 Searcher output for coverage completeness.

**When applicable:** Always — in 95%+ of runs, the Reviewer passed with "coverage looks complete". Fallback: if a downstream Writer flags `MISSING CONTEXT: <subsystem>`, redispatch the Searcher with the gap before continuing. Slower on the 5% bad-case path; faster on the 95% good-case path.

**`--thorough` behavior:** RESTORES the coverage Reviewer. Step 2 reverts to Worker + Reviewer pattern for coverage validation.

---

### L5 — Drop dispatch wrap-up Reviewer (D5)

**What it is:** Remove the Opus Reviewer from dispatch Step 4 (delete task file + append memory entry + chore commit). Step 4 executes inline by the orchestrator; no Reviewer dispatch.

**When applicable:** Always for wrap-up — this work is mechanically simple and already validated by per-batch reviewers and the final integration review. Iron rule updates from `≥ batches + 2` to `≥ batches + 1`.

**`--thorough` behavior:** RESTORES the wrap-up Reviewer. Dispatch Step 4 reverts to Worker + Reviewer pattern. Iron rule reverts to `≥ batches + 2`.

---

### L6 — Default L1-L2 cap (D6)

**What it is:** Batched Reviewer level cap defaults to L1-L2 (was L1-L3 in practice). Triage flags `security: bool` or `integration_risk: bool` elevate the cap to L1-L3+ when warranted.

**When applicable:** Standard complexity tasks without security or integration flags. L3 adds integration/security checks; L4 adds perf; L5 adds a11y — most doc edits, small refactors, and config changes don't need L3 review.

**`--thorough` behavior:** Elevates default cap to L1-L3. All batches reviewed at L3 regardless of triage flags.

---

### L7 — Conditional final integration review (D7)

**What it is:** Skip the final integration review when all batches passed first-try AND no escalations AND no security flags fired. Print `"Final integration review skipped — all batches PASSed first try"` and proceed to Step 4.

**When applicable:** Triggered when `all_batches_passed_first_try AND no_escalations AND no_security_flags`. If ANY batch had ≥1 NEEDS_FIX retry, ANY escalation fired, or ANY security flag tripped → integration review runs unconditionally.

**`--thorough` behavior:** Disables the skip entirely. Final integration review always runs regardless of batch outcomes.

---

### L8 — Aggressive P4 thresholds (D8)

**What it is:** P4 triage thresholds tightened — skip multi-dim Analyst at `ambiguity < 0.6` (was 0.4); bounce to scope at `ambiguity < 0.4` (was 0.2). Requests at ambiguity 0.4-0.6 operationally rarely benefit from multi-dim analysis. The 2-question floor (Step 4) is preserved non-negotiably.

**When applicable:** Whenever `ambiguity < 0.6 AND complexity != high` (skip multi-dim) or `ambiguity < 0.4 AND complexity == low` (bounce). Borderline rounding rule unchanged: round up on the fence — never skip on ambiguous boundary cases.

**`--thorough` behavior:** Reverts to round-1 thresholds: skip multi-dim at `ambiguity < 0.4`; bounce at `ambiguity < 0.2`. All ceremony runs on higher-ambiguity cases.

---

### L9 — DOCTRINE §12.1 trivial inline (D9)

**What it is:** §12.1 amendment to DOCTRINE §12 — trivial steps (≤ 2 tool calls, no content generation, no decision-making, no review needed, orchestrator is the natural executor) may be performed inline by the orchestrator without an Agent dispatch wrapper. Examples: dispatch Step 4 wrap-up (delete + memory append + commit), scope hand-off invocations, spec hand-off.

**When applicable:** Only when ALL five §12.1 criteria are met. Non-trivial steps (any code/doc generation, multi-file change, cross-file consistency reasoning, research/Read of unfamiliar context, Reviewer-eligible output) remain Agent-dispatched per §12. Trivial-eligibility is checked at step-start; if the orchestrator discovers mid-step that the work needs generation/research, it MUST abort the inline path and dispatch an Agent.

**`--thorough` behavior:** Disables §12.1 entirely. All steps Agent-dispatched as in round 1 — no inline execution regardless of triviality.

---

## When to disable

### Round 1 patterns

| Flag | Disables | Keeps |
|---|---|---|
| `--thorough` / `depth=max` | P1, P2, P4 | P3, P5 |
| (none) | — | All five on |

P3 and P5 are always on because they carry no quality tradeoff. P1, P2, and P4 restructure dispatch shape and skip steps; `--thorough` restores sequential drafts, per-section reviews, and full step execution.

**Exception within P1:** scope Step 2's parallel Searchers stay on even under `--thorough`. They are independent reads with no ordering dependency, so serializing them yields no quality gain. Only P1 surfaces with plausible section-order coupling are serialized by `--thorough` (spec §7 Writer sections, scope Step 4 Writer-internal sections).

### Round 2 levers

| Lever | Default | `--thorough` restores |
|---|---|---|
| L1 — Haiku Classifier | On (Haiku tier) | No change — Haiku stays |
| L2 — Combined audit+deploy gate | On (1 round-trip) | No change — combined gate stays |
| L3 — Session-cached context | On (bundle) | No change — bundle stays |
| L4 — Drop spec Searcher coverage Reviewer | On (no Reviewer) | Step 2 coverage Reviewer restored |
| L5 — Drop dispatch wrap-up Reviewer | On (inline only) | Wrap-up Reviewer restored; iron rule reverts to `≥ batches + 2` |
| L6 — Default L1-L2 cap | On (L1-L2 default) | Cap elevated to L1-L3 default |
| L7 — Conditional integration review | On (skippable when all green) | Integration review always runs |
| L8 — Aggressive P4 thresholds | On (skip at 0.6 / bounce at 0.4) | Reverts to round-1 thresholds (skip at 0.4 / bounce at 0.2) |
| L9 — §12.1 trivial inline | On (inline-allowed) | §12.1 disabled; all steps Agent-dispatched |

---

## Quality preservation

### Round 1 (structural)

Round 1 patterns do not change:
- Which tier reviews what — Opus reviewers remain on every Worker output (P2 consolidates calls, does not eliminate them)
- Review level caps — L1–L5 assignments per sub-task are unchanged
- Worker access to context — workers still reach full doctrine and project context via `.hyperflow/memory/` (P5 makes access on-demand, not absent)
- Step coverage on ambiguous requests — P4 skips only on low-ambiguity, and rounds up on borderline cases

What changes is **structure**: when calls fire, in what grouping, with what prompt payload. The quality floor is held by the Reviewer still seeing every output and workers retaining full context access.

### Round 2 (count + tier)

Round 2 acknowledges a narrow tradeoff: **orchestration ceremony** (wrap-up, conditional integration review, trivial inline steps) is relaxed; **implementation work** is not.

What round 2 does NOT change:
- Implementation work still hits an Opus per-batch Reviewer (L5 drops the wrap-up Reviewer, not the batch Reviewer)
- Per-sub-task commit cadence — preserved unconditionally
- SECURITY_VIOLATION halt — preserved unconditionally
- 2-question spec floor (Step 4) — preserved unconditionally even when P4/L8 skip other ceremony
- Borderline rounding rule — preserved (round up on ambiguity boundary; never skip on the fence)

What round 2 relaxes:
- Opus reviewing mechanical orchestration steps (delete task file, memory append, chore commit) — L5 + L9
- A final integration review that would redundantly check already-green first-try batches — L7
- A coverage Reviewer over a Searcher output that passes at 95%+ rate — L4
- Opus tier for structured JSON classification (Haiku is adequate) — L1

The net: implementation Opus calls are unchanged. Orchestration Opus calls drop by 2-3 per median chain. `--thorough` restores L4, L5, L7, L8, L9 for runs where maximum ceremony is warranted.
