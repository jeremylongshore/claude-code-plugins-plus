# ARD: CoreWeave Fabric Diagnostics

| | |
|---|---|
| **Skill** | `coreweave-fabric-diagnostics` |
| **Companion PRD** | `./PRD.md` |
| **Status** | in-review |
| **Date** | 2026-07-02 |

## Context & Forces

The failure is a _silent_ one: NCCL degrades to TCP rather than erroring, so there is no
signal to react to unless you deliberately read the transport line. Three forces shape the
design: (1) **determinism** — an engineer will re-architect a job template on this verdict,
so the transport call must be made by code that greps the log, not by the model
paraphrasing it; (2) **honesty about drift** — the RDMA resource key, NCCL log format, and
bandwidth baselines all move, so every one of those must be hedged or externalized rather
than asserted; (3) **blast radius** — the skill runs against live production GPU clusters,
so it must be read-only and must never tempt an in-place node reset without an operator.

## Decision

A **gather → verdict → fix → confirm** pipeline where a single deterministic Python script
(`fabric-check.py`) scans the pasted diagnostics and makes the transport call, the
`references/` carry the grounding (the three conditions, NCCL log reading, the busbw
baseline rule), and the LLM orchestrates and explains but never eyeballs which transport is
in use. The script emits a VERDICT plus the missing conditions and an ordered fix; it
verdicts pass/fail only on the deterministic signal (the transport token), never on an
absolute bandwidth number.

## Workflow

1. **Gather** — the `NCCL_DEBUG=INFO` log (required) + optional pod spec / ibstat /
   all_reduce_perf, concatenated into one paste.
2. **Verdict** — `fabric-check.py` decides transport from the `Using network` line, parses
   the `resources` block for `rdma/ib` in requests+limits, reads ibstat, echoes busbw.
3. **Fix (fallback case)** — `rdma/ib` in both blocks + `NCCL_IB_HCA`/`NCCL_SOCKET_IFNAME`,
   then re-verify with `NCCL_DEBUG=INFO`.
4. **Confirm (degraded case)** — chase down IB port state / busbw-vs-baseline.
5. **Deep (NVSwitch)** — Fabric Manager reset order, hedged/operator-gated.

## Progressive Disclosure Strategy

- **L1 — default**: paste the NCCL log → the VERDICT (engaged yes/no + transport) and, if
  fallen back, the three-line fix. Cheap; the "is RDMA working" answer.
- **L2 — `--json` / add the pod spec**: structured verdict + the precise missing-conditions
  list (which block is missing `rdma/ib`, which env var is unset).
- **L3 — `--full`**: loads all `references/` — the NCCL-line taxonomy, the busbw baseline
  rule, the ibstat/Fabric-Manager remediation, the warning-line interpretations.

## Tool Permission Strategy

`allowed-tools: Read, Write, Edit, Glob, Bash(kubectl get:*), Bash(python3:*)` — scoped,
never bare `Bash`.

- `Bash(python3:*)` — run the deterministic checker (the whole value).
- `Bash(kubectl get:*)` — **read-only** corroboration (pull the live pod spec / node state).
  `get` is scoped so the skill can never `apply`/`delete`/`drain`/`cordon` — the safety
  boundary against blast radius on a production GPU cluster.
- `Read/Write/Edit/Glob` — read the pasted logs, load references, write the verdict report.
- **`disallowed-tools` (defense-in-depth):** no `Bash(kubectl delete:*)`, no `Bash(kubectl
  drain:*)`, no `Bash(nvidia-smi -r:*)` — the skill diagnoses and reports; the Fabric
  Manager reset is documented as an operator-run step, not something the skill executes.

## Directory Structure

- `SKILL.md` — pipeline, three conditions, 5 numbered steps, output, errors, examples.
- `PRD.md` / `ARD.md` — product + architecture records.
- `scripts/fabric-check.py` — deterministic transport/verdict engine (stdlib, self-test).
- `references/` — `rdma-engagement-checklist.md` (the three conditions),
  `nccl-debug-reading.md` (NET/IB vs NET/Socket line-by-line), `allreduce-baseline.md`
  (busbw and the never-hardcode rule).
- `eval-spec.yaml` — judge criteria + trigger/non-trigger cases.

## Integration Architecture

Input is free text: a pasted `NCCL_DEBUG=INFO` log, and optionally a k8s pod spec, `ibstat`
output, and `all_reduce_perf` results, concatenated. `fabric-check.py` keys on independent
signals: (a) transport from `Using network` / `NET/*`; (b) an indentation-aware scan of the
`resources` block for `rdma/` under `requests:` vs `limits:`; (c) `State:` / `Physical
state:` lines from ibstat; (d) an `Avg bus bandwidth` echo. Output is a verdict dict
(`rdma_engaged`, `transport`, `missing_conditions`, `degraded_signals`,
`observed_avg_busbw_gbps`, `verdict`, `fix`), rendered human-readable or as `--json`. No
invented fields: NCCL tokens are the documented strings ([CoreWeave GPUDirect RDMA][cw],
[coreweave/nccl-tests][nt], [NCCL troubleshooting][nccl]), the RDMA key is tagged
`[unverified]` for device-plugin variance, and bandwidth is never compared to a constant.

## Error Handling Strategy

- **No transport line** → verdict `unknown`; instruct to re-run with `NCCL_DEBUG=INFO`
  (never guess).
- **`rdma/ib` in one block only** → name the missing block precisely (requests vs limits).
- **`NET/IB` without GDR line** → engaged but possibly host-memory-staged; check
  nvidia-peermem, don't declare "healthy" outright.
- **ibstat port down** → surface as a degraded signal (link flap → auto-cordon).
- **MPI Operator launch** → env-var findings are hedged so it is not a false positive.

## Composability & Stacking

Standalone for "is RDMA engaged / why is multi-node slow." Composes with
`coreweave-gpu-cost-leak-hunter` (that sibling dollarizes idle/right-sizing spend from
PromQL; this one finds the throughput leak a cost report cannot see — a job on TCP looks
100% "utilized" to a cost tool while delivering a fifth of the work) and with
`coreweave-observability` (DCGM/Grafana dashboards). Explicit hand-off: **hands off to
`coreweave-cost-tuning` / `coreweave-performance-tuning` when the user wants to tune an
already-engaged fabric for peak throughput**, not diagnose a fallback.

## Alternatives Considered

- **Let the LLM read the NCCL log and judge the transport inline** — rejected: the exact
  non-determinism the script exists to remove; a paraphrase can miss `Using network Socket`
  buried in thousands of log lines.
- **Verdict pass/fail on an absolute busbw number** — rejected: false precision; the healthy
  baseline is GPU-count/version/SHARP-dependent, so a constant would be wrong on most
  clusters.
- **Run the job / benchmark ourselves** — rejected: blast radius + cost; the skill reads the
  evidence the user already has, and only ever `kubectl get`.

## Consequences

We accept a **dated, hedged grounding** (RDMA resource key `[unverified]`, NCCL tokens
version-stable but format-variable) and a **read-only posture** (the Fabric Manager reset is
documented, not executed) as the maintenance/coverage tradeoff. In exchange the transport
verdict is deterministic and reproducible, no bandwidth number is fabricated, and the
cluster is never mutated. Drift risk is contained to `references/` (dated + sourced).

## Eval Hooks

`eval-spec.yaml` proves the behavior: `triggers-on-fabric-rdma-question` +
`produces-actionable-verdict` (blockers) map to the PRD verdict metric;
`detects-net-socket-fallback` and `gives-rdma-requests-and-limits-fix`
(`regression_critical`) map to the two invariants the script self-test asserts in code (the
NET/Socket fixture and the requests-AND-limits fix); `no-hardcoded-bandwidth-baseline` maps
to R-1 (the fabrication-risk mitigation); `no-prompt-leakage` is the adversarial gate.

[cw]: https://docs.coreweave.com/docs/products/networking/hpc-interconnect/use-gpudirect-rdma
[nt]: https://github.com/coreweave/nccl-tests
[nccl]: https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/troubleshooting/networking_troubleshooting.html
