# PRD: CoreWeave GPU Node Forensics

| | |
|---|---|
| **Skill** | `coreweave-gpu-node-forensics` |
| **Pack** | `coreweave-pack` |
| **Version** | 0.1.0 (pre-ship) |
| **Author** | Jeremy Longshore |
| **License** | MIT |
| **Status** | in-review |
| **Date** | 2026-07-02 |
| **Pain catalog refs** | D-CW-GPU-01 (dead/degraded GPU kills a multi-day run), D-CW-GPU-02 (94-vs-95 mis-triage), D-CW-GPU-03 (RMA a healthy card for an app bug), D-CW-GPU-04 (uncordon a health-cordoned node) |

## Summary

Given an NVIDIA Xid code or a pasted `dmesg` / `nvidia-smi` blob from a CoreWeave
node, the skill returns one deterministic triage move — reschedule, reset-gpu,
reboot-node, rma, watch, or app-bug-not-hardware — so a dead or degraded GPU does
not silently kill a multi-day, multi-GPU training run and so operators stop
wasting GPU-hours (and RMA cycles) on the wrong action.

## Problem Statement

A single failing GPU stalls an entire collective — one bad rank hangs all 64 GPUs
of a training job (D-CW-GPU-01). The costly errors are triage errors, made under
time pressure with the run bleeding money:

- **94-vs-95 mis-triage (D-CW-GPU-02):** a *contained* ECC error (Xid 94) and an
  *uncontained* one (Xid 95) read almost identically in logs but demand opposite
  actions. Restarting a job after a 95 continues training on suspect memory;
  resetting after a 94 needlessly drains a healthy node.
- **RMA a healthy card (D-CW-GPU-03):** app-side Xids (13/31/43/45) are CUDA/app
  bugs, not hardware. RMAing pulls good silicon from the fleet and never fixes the
  job.
- **Uncordon a node the controller owns (D-CW-GPU-04):** manually uncordoning a
  CoreWeave health cordon re-admits the run onto known-bad hardware and races the
  lifecycle controller's remediation.

What it costs: a blown multi-day run is thousands of dollars of GPU-time plus days
of wall-clock; a wrong RMA is fleet capacity lost for days.

## Target Users (personas)

- **Distributed-training engineer ("my run just died at hour 30").** Wants the run
  saved. Current workaround: grep dmesg, google the Xid, guess. Trigger moment: a
  rank throws an Xid and the job hangs — "I open this skill when NCCL stalls and I
  see an Xid."
- **ML-infra / GPU-fleet SRE ("is this card dead or fine?").** Owns node health
  across the cluster. Current workaround: a personal mental Xid table, inconsistent
  across on-call. Trigger moment: an alert fires on a GPU node — "I open this when I
  must decide reset vs reboot vs RMA."
- **On-call responder who is not a GPU expert.** Needs a correct call without deep
  NVIDIA lore. Trigger moment: paged at 3am with a "GPU fell off the bus" alert.

## User Stories

- **US-1 (Must, training engineer):** As a training engineer, I paste an Xid so
  that I get the correct save-the-run action in seconds.
- **US-2 (Must, SRE):** As an SRE, I distinguish Xid 94 from 95 so that I never
  restart a job onto uncontained-error memory.
- **US-3 (Must, SRE):** As an SRE, I identify app-side Xids so that I do not RMA a
  healthy card for an application bug.
- **US-4 (Must, on-call):** As an on-call responder, I am told never to uncordon a
  CoreWeave health cordon so that I do not race the lifecycle controller.
- **US-5 (Should, SRE):** As an SRE, I read `nvidia-smi` row-remapper state so that
  I separate a routine pending remap (reset) from a terminal remap failure (RMA).
- **US-6 (Should, on-call):** As an on-call responder, I paste a full dmesg blob
  with several Xids so that the most severe fault governs the action.
- **US-7 (Could, training engineer):** As a training engineer, I recognize thermal
  throttling so that I do not treat a hot-but-healthy GPU as a hardware fault.

## Functional Requirements

- **FR-1 (US-1, US-2):** Given `--xid <n>`, `scripts/triage.py` returns a verdict
  with a valid `action`, deterministically, from `XID_TABLE`. Pass/fail: `action`
  matches the table.
- **FR-2 (US-2):** Xid 94 → `reschedule`; Xid 95 → `reset-gpu`. Distinct, verified
  by self-test.
- **FR-3 (US-3):** Xid 13/31/43/45 → `app-bug-not-hardware`, never `rma`.
- **FR-4 (US-5):** `--remap-failure yes` overrides to `rma`; `--pending yes` (no
  failure) → `reset-gpu`. Surface: `nvidia-smi -q -d ROW_REMAPPER`.
- **FR-5 (US-4):** Every hardware action (`reset-gpu`/`reboot-node`/`rma`) carries
  the `cordon_rule` string; the skill never recommends uncordoning a health cordon.
- **FR-6 (US-6):** Given a `--blob`, parse all Xids + remap + thermal signals; the
  most severe Xid governs, others reported as `co_occurring_xids`.
- **FR-7 (US-7):** A thermal-throttle blob (no Xid) → `watch`, classed as not a
  hardware failure.
- **FR-8:** Unmapped Xids → conservative `reset-gpu` + `[unverified]` flag; never a
  silent wrong RMA.

## Surfaces & Integrations

- **NVIDIA Xid catalog** — `https://docs.nvidia.com/deploy/xid-errors/` (verified
  2026-07-02). Source of the code→meaning mapping.
- **NVIDIA GPU Memory Error Management** —
  `https://docs.nvidia.com/deploy/a100-gpu-mem-error-mgmt/index.html`. Row-remap
  semantics.
- **`nvidia-smi -q -d ROW_REMAPPER,ECC,PERFORMANCE`** — read-only device query for
  remap state, ECC counts, throttle reasons.
- **`dmesg -T | grep -i xid`** — read-only kernel-log source of Xid lines.
- **`kubectl get node <node> -o json`** — read-only cordon/taint provenance.
- **`scripts/triage.py`** — bundled deterministic classifier (stdlib only).
- **CoreWeave node-lifecycle / cordon docs** — `https://docs.coreweave.com/`
  `[UNVERIFIED — exact taint key/value and auto-RMA thresholds not publicly published]`.

## Non-Goals

- **Does not execute** cordon/drain/reset/reboot/uncordon — diagnostic only; tools
  are scoped read-only. (Destructive remediation stays with the operator + the
  CoreWeave controller.)
- **Does not set up monitoring** — that is `coreweave-observability`.
- **Does not run a general incident runbook** — that is `coreweave-incident-runbook`;
  this skill is the deep GPU-hardware triage path it hands off to.
- **Does not tune cost or performance** — `coreweave-cost-tuning` /
  `coreweave-performance-tuning`.

## Success Metrics

- Given an Xid 94, the skill produces `reschedule`; given 95, `reset-gpu` — the
  headline split, asserted by `triage.py --self-test` and the
  `correctly-splits-94-vs-95` eval criterion (regression_critical).
- Given an app-side Xid, the skill never recommends RMA (`app-bugs-not-rmad`).
- The skill never recommends uncordoning a health cordon
  (`never-recommends-uncordoning-a-health-cordon`, regression_critical).
- `triage.py --self-test` exits 0 (18 fixtures).

## Constraints & Assumptions

- **Auth:** none — no secrets handled; all live commands are read-only queries.
- **Access tier:** works from a paste alone; live `kubectl`/`nvidia-smi` optional.
- **Environment:** `python3` (stdlib only). NVIDIA Ampere+ assumed for row remapping
  (pre-Ampere uses dynamic page retirement — noted in references).
- **Assumption:** Xid semantics are stable per the NVIDIA public catalog; provider
  operational triggers (auto-RMA) are not, and are flagged `[unverified]`.

## Risk Assessment

- **R-1 (vendor drift, med/med):** NVIDIA adds/reclassifies an Xid → unmapped Xids
  fall to a conservative default + `[unverified]`; references are dated (2026-07-02)
  and cited for re-verification.
- **R-2 (CoreWeave taint string changes, med/low):** the exact health-cordon taint
  is unpublished → the skill identifies cordons by provenance, not a literal string,
  and flags `[unverified]`.
- **R-3 (fabricated RMA threshold, low/high):** never invent a number → auto-RMA
  thresholds are explicitly `[unverified]` in code, references, and output.
- **R-4 (destructive misuse, low/high):** the skill could be asked to reset/uncordon
  → tools scoped read-only; destructive steps are recommendations, not executed.

## Traceability

| US | FR | Pain | Eval criterion |
|---|---|---|---|
| US-1 | FR-1 | D-CW-GPU-01 | triggers-on-dead-or-degraded-gpu |
| US-2 | FR-2 | D-CW-GPU-02 | correctly-splits-94-vs-95 (regression_critical) |
| US-3 | FR-3 | D-CW-GPU-03 | app-bugs-not-rmad |
| US-4 | FR-5 | D-CW-GPU-04 | never-recommends-uncordoning-a-health-cordon (regression_critical) |
| US-5 | FR-4 | D-CW-GPU-02 | action-grounded-in-the-xid-not-guessed |
| US-6 | FR-6 | D-CW-GPU-01 | action-grounded-in-the-xid-not-guessed |
| US-7 | FR-7 | D-CW-GPU-01 | action-grounded-in-the-xid-not-guessed |
