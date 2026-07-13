# ARD: CoreWeave GPU Node Forensics

| | |
|---|---|
| **Skill** | `coreweave-gpu-node-forensics` |
| **Companion PRD** | `./PRD.md` |
| **Status** | in-review |
| **Date** | 2026-07-02 |

## Context & Forces

The skill fires at the worst moment: a multi-day, multi-GPU run has stalled, the
clock is burning GPU-dollars, and the operator must choose one of six irreversible-
ish actions from an opaque Xid code. The forces:

- **Blast radius is huge and asymmetric.** A wrong "just reschedule" after an Xid 95
  silently corrupts a run; a wrong "RMA" on an app-side Xid pulls healthy silicon.
- **The signals look alike.** Xid 94 and 95 are both "ECC errors" in casual logs;
  the containment bit is the whole decision.
- **The operator is stressed and may not be a GPU expert.** The answer must be
  correct without deep NVIDIA lore, and must resist the instinct to uncordon a
  stuck node.
- **Vendor surface drifts.** NVIDIA reclassifies Xids; CoreWeave's operational
  triggers are unpublished. The skill must not fabricate.

## Decision

Split the problem into a **deterministic classifier** (`scripts/triage.py`, the
single source of truth for Xid→action and row-remap overrides) and an **LLM
reasoning layer** (SKILL.md) that captures evidence, invokes the classifier, and
explains/acts on the verdict in plain language. The LLM never decides the action;
it drives the workflow around a decision the code owns. This is the
deterministic-core / probabilistic-shell pattern the pack's value skills share.

## Workflow

1. **Capture** — obtain the Xid code or a pasted `dmesg` / `nvidia-smi` blob
   (works from a paste alone; live queries optional).
2. **Classify** — run `python3 scripts/triage.py` with `--xid` (+ optional
   `--pending`/`--remap-failure`) or `--blob`. The script parses, picks the
   governing signal, applies the row-remap override, and emits verdict JSON.
3. **Explain** — render the `action` + `why` + `next_command` in plain language;
   state the 94-vs-95 call explicitly when it applies.
4. **Guard** — for any hardware action, surface the cordon hard rule verbatim.
5. **Act** — hand the operator the single next command (the skill recommends;
   it does not execute destructive steps).

## Progressive Disclosure Strategy

- **L1 — default:** `triage.py --xid <n>` → the verdict block. Cheap, no references
  loaded, covers the common "what does this Xid mean and what do I do."
- **L2 — `--pending`/`--remap-failure` or `--blob`:** adds row-remapper reasoning
  and multi-Xid blob parsing; loads `row-remap-decision.md` when the case is a
  remap/DBE.
- **L3 — full:** loads `xid-triage-table.md` (the complete catalog + escalation
  ladder) and `cordon-rules.md` (provenance + safe operator path) for an
  exhaustive walk-through.

## Tool Permission Strategy

`allowed-tools: Read, Bash(python3:*), Bash(nvidia-smi -q:*), Bash(kubectl get:*), Bash(dmesg:*)`

- `Bash(python3:*)` — run the bundled classifier.
- `Bash(nvidia-smi -q:*)` — **query mode only.** The `-q` scope deliberately
  excludes `nvidia-smi -r` (GPU reset) and other mutating forms.
- `Bash(kubectl get:*)` — read-only node/taint inspection; excludes
  `kubectl cordon/uncordon/drain`.
- `Bash(dmesg:*)` — read kernel log.
- `Read` — read pasted blobs and evidence files. No write surface: the skill is
  diagnostic and never mutates cluster or filesystem state.

**`disallowed-tools` (defense in depth):** bare `Bash`, `Bash(nvidia-smi -r:*)`,
`Bash(kubectl cordon:*)`, `Bash(kubectl uncordon:*)`, `Bash(kubectl drain:*)`,
`Bash(reboot:*)`. **Safety justification:** the entire class of destructive
remediation (reset, reboot, cordon changes) is owned by the operator and the
CoreWeave lifecycle controller; the skill must be incapable of executing an
uncordon or a reset itself. It recommends; it never pulls the trigger.

## Directory Structure

- `SKILL.md` — the workflow + reasoning layer.
- `PRD.md` / `ARD.md` — this skill's product + architecture record.
- `scripts/triage.py` — deterministic classifier + `--self-test` (stdlib only).
- `references/xid-triage-table.md` — full code→action table (dated, cited).
- `references/row-remap-decision.md` — `ROW_REMAPPER` routine-vs-terminal logic.
- `references/cordon-rules.md` — CoreWeave health-cordon ownership + safe path.
- `eval-spec.yaml` — judge criteria + regression-critical criteria + self-test hook.

## Integration Architecture

Two evidence planes, both read-only:

- **Paste plane (primary):** the user pastes `dmesg` / `nvidia-smi` text. `triage.py`
  parses it with anchored regexes (`Xid\s*(?:\(...\))?\s*[:,]?\s*(\d+)`,
  `Remapping Failure Occurred : (Yes|No)`, `Pending : (Yes|No)`, thermal-slowdown).
  No network, no cluster.
- **Live plane (optional corroboration):** `nvidia-smi -q` on the node,
  `kubectl get node` for cordon provenance. Never required.

Error taxonomy is grounded in real codes — Xid 13/31/43/45/48/63/64/74/79/92/94/95/
119/120 and the `Remapping Failure Occurred` / `Pending` fields — no invented
fields. Request→response shape: text in, verdict JSON out.

## Error Handling Strategy

- **Unmapped Xid** → conservative `reset-gpu` default + `[unverified]` flag (never a
  silent wrong RMA).
- **94 vs 95** → decided by exact code only; the skill refuses to infer containment
  from prose.
- **Multiple Xids** → most-severe governs (severity rank), others surfaced.
- **No signal** → `watch` + request for fresh evidence, not a fabricated verdict.
- **Unpublished provider facts** (auto-RMA thresholds, taint strings) → surfaced as
  `[unverified]`, never guessed.

## Composability & Stacking

Standalone: paste an Xid, get a verdict. In-pack: `coreweave-observability` surfaces
the Xid → this skill triages it → `coreweave-incident-runbook` runs the broader
incident. Hands off to `coreweave-incident-runbook` when the problem is a
multi-service incident rather than a single-GPU decision, and to
`coreweave-performance-tuning` when the finding is thermal throttling worth chasing
in cooling/scheduling rather than a fault.

## Alternatives Considered

- **LLM classifies the Xid directly (no script).** Rejected — the 94-vs-95 bit is
  too load-bearing to trust to token-level reasoning; a deterministic table is
  auditable and regression-testable.
- **Skill executes the remediation (cordon/reset).** Rejected — unacceptable blast
  radius; violates the CoreWeave cordon-ownership rule. Diagnostic-only is the point.
- **One giant Xid reference, no script.** Rejected — the value is a *decision*, not a
  lookup; the script forces a single action out.
- **Vendor MCP dependency.** Rejected — no stable public CoreWeave GPU-health MCP;
  paste-first keeps the skill usable with zero setup.

## Consequences

- **Accepted:** the Xid table must be maintained against NVIDIA catalog drift
  (dated references + unmapped-default cushion the cost).
- **Accepted:** provider operational facts stay `[unverified]` until CoreWeave
  publishes them — honesty over false precision.
- **Accepted:** read-only scoping means the operator runs the destructive step
  themselves — by design, this is a feature (blast-radius control), not a gap.

## Eval Hooks

`eval-spec.yaml` proves the behavior on two levels:

- **Deterministic (`self_test`):** `python3 scripts/triage.py --self-test` — 18
  fixtures asserting 94→reschedule, 95→reset-gpu, 79→reboot-node, 43/13/31→app-bug,
  remap-failure→rma, remap-pending→reset-gpu, cordon-rule-present on hardware
  actions. Exit 0 required.
- **Judge:** `triggers-on-dead-or-degraded-gpu` (blocker),
  `correctly-splits-94-vs-95` (regression_critical),
  `never-recommends-uncordoning-a-health-cordon` (regression_critical),
  `action-grounded-in-the-xid-not-guessed`, `app-bugs-not-rmad`, `no-prompt-leakage`
  (blocker). Every PRD success metric maps to one of these criteria.
