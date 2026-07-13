# PRD: CoreWeave Fabric Diagnostics

| | |
|---|---|
| **Skill** | `coreweave-fabric-diagnostics` |
| **Pack** | `coreweave-pack` |
| **Version** | 0.1.0 (pre-ship) |
| **Author** | Jeremy Longshore |
| **License** | MIT |
| **Status** | in-review |
| **Date** | 2026-07-02 |
| **Pain catalog refs** | CW-F1 silent TCP fallback, CW-F2 missing rdma/ib request, CW-F3 unset NCCL env, CW-F4 degraded/flapping IB link |

## Summary

Detects the single most expensive silent failure on a CoreWeave multi-node GPU job:
GPUDirect RDMA falling back from InfiniBand (`NET/IB`) to TCP (`NET/Socket`). The fallback
raises no error but collapses collective throughput (commonly 5-20x) while every GPU still
bills at full rate. From a pasted `NCCL_DEBUG=INFO` log (and/or pod spec / ibstat /
all_reduce_perf), a deterministic script verdicts whether RDMA is engaged and gives the fix.

## Problem Statement

Multi-node NCCL is designed to **degrade rather than fail** — if it cannot bring up the IB
transport it uses TCP sockets so the job still completes ([NCCL troubleshooting][nccl]). On
a single node that is harmless; across nodes it means every all-reduce crosses the Ethernet
control plane instead of the InfiniBand fabric, and end-to-end throughput drops 5-20x with
no error surfaced. Teams see "training is slow" and burn days (and 5x the GPU-hours for the
same work) before anyone checks the transport line. The failure hides behind four causes:
(CW-F1) NCCL logged `NET/Socket` and nobody read it; (CW-F2) the `rdma/ib` device was not
requested in both `resources.requests` and `resources.limits`, so the device plugin never
injected the HCA; (CW-F3) `NCCL_IB_HCA`/`NCCL_SOCKET_IFNAME` unset (outside the MPI
Operator); (CW-F4) an IB link is down/flapping and CoreWeave auto-cordoned the node.

## Target Users (personas)

- **Dana — ML engineer running distributed training.** Owns the training job; not an IB/HPC
  specialist. Current workaround: stares at loss curves and step time, assumes "the cluster
  is slow." Trigger moment: *"I open this skill when a multi-node run is inexplicably slower
  than the single-node math predicts."*
- **Sam — platform/infra engineer for the GPU cluster.** Fluent in kubectl and NCCL, owns
  the manifests. Current workaround: manually greps NCCL logs and eyeballs ibstat.
  Trigger moment: *"I open this skill to confirm RDMA engaged before I sign off a new job
  template."*

## User Stories

- **US-1 (Must)** — As Dana, I paste my NCCL log and get a yes/no verdict on whether RDMA is
  engaged, so I know if the slowness is a fabric fallback. → CW-F1
- **US-2 (Must)** — As Sam, when it fell back I get the exact fix — `rdma/ib` in BOTH
  requests and limits + the NCCL env vars — so I can correct the manifest. → CW-F2, CW-F3
- **US-3 (Must)** — As Dana, the transport call is made deterministically by a script, not
  the model eyeballing the log, so I trust the verdict. → all
- **US-4 (Should)** — As Sam, when RDMA is engaged but slow, the skill surfaces degraded
  signals (down IB port, low busbw) without inventing a baseline number. → CW-F4
- **US-5 (Should)** — As Sam, any all-reduce bandwidth figure is compared to CoreWeave's
  nccl-tests manifest baseline, never a hardcoded constant. → CW-F4

## Functional Requirements

- **FR-1** — Parse a pasted `NCCL_DEBUG=INFO` log and decide the transport from the decisive
  `Using network` line (falling back to `NET/IB` vs `NET/Socket` counts).
  (Surface: `Bash(python3:*)` → `scripts/fabric-check.py`) → US-1/US-3 → `detects-net-socket-fallback`
- **FR-2** — Parse a k8s `resources` block (indentation-aware) and flag `rdma/ib` missing
  from `requests` or `limits` precisely. → US-2 → `gives-rdma-requests-and-limits-fix`
- **FR-3** — Flag `NCCL_IB_HCA`/`NCCL_SOCKET_IFNAME` unset (hedged for the MPI Operator) and
  `NCCL_IB_DISABLE=1`. → US-2 → `gives-rdma-requests-and-limits-fix`
- **FR-4** — Parse `ibstat` and flag ports not `State: Active` / `Physical state: LinkUp`
  (link down / flap → auto-cordon). → US-4 → `produces-actionable-verdict`
- **FR-5** — Echo any `all_reduce_perf` `Avg bus bandwidth` tagged `[unverified vs
  baseline]`; never verdict pass/fail on an absolute number. → US-5 → `no-hardcoded-bandwidth-baseline`
- **FR-6** — Emit a VERDICT (`rdma_engaged` yes/no/partial/unknown + transport), the missing
  conditions, and the ordered fix; `--json` for structured output; `--self-test` with
  fixtures. → US-1/US-2 → `produces-actionable-verdict`

## Surfaces & Integrations

- **NCCL log tokens** — `Using network IB` / `Using network Socket`, `NET/IB`, `NET/Socket`,
  `GPU Direct RDMA Enabled` / `GDRDMA`, `NCCL WARN ... ibv_*` (verbatim NCCL strings; exact
  format is version-dependent `[UNVERIFIED — tokens stable, surrounding format varies]`).
- **NCCL env vars** — `NCCL_IB_HCA=ibp`, `NCCL_SOCKET_IFNAME=eth0` ([CoreWeave GPUDirect
  RDMA doc][cw]); `NCCL_IB_DISABLE`, `NCCL_NET_GDR_LEVEL` ([NCCL env][env]).
- **k8s resource key** — `rdma/ib` in `resources.{requests,limits}` [UNVERIFIED — exact key
  depends on the installed RDMA device plugin; confirm via `kubectl describe node`].
- **kubectl** — `kubectl get pod -o yaml` (read-only) to pull the live spec.
- **nccl-tests** — `all_reduce_perf` busbw/algbw ([coreweave/nccl-tests][nt]).
- **Script** — `scripts/fabric-check.py` (stdlib only).

## Non-Goals

- **Does not tune NCCL for peak throughput** (QPS-per-connection, GDR levels, SHARP) — that
  is deeper perf work; this skill answers "is RDMA engaged at all, and if not why."
- **Does not mutate the cluster** — read-only detection + a report; never `kubectl
  apply`/`delete`/`drain`, never an in-place GPU reset without an explicit operator.
- **Does not benchmark for you** — it reads the `all_reduce_perf` you ran; it does not launch
  the job.
- **Does not dollarize spend** — that is the sibling `coreweave-gpu-cost-leak-hunter`.

## Success Metrics

- Given a `NET/Socket` log, the skill verdicts `rdma_engaged: no` + transport `Socket`
  (asserted by the script self-test fixture).
- Given a `NET/IB` + GDR log, it verdicts `rdma_engaged: yes` (self-test fixture).
- Given a manifest with `rdma/ib` in only one of requests/limits, it flags the missing block
  (self-test fixture).
- Any busbw figure is hedged as `[unverified vs baseline]` (`no-hardcoded-bandwidth-baseline`).

## Constraints & Assumptions

- Auth from env (`$KUBECONFIG` for optional read-only corroboration); no secrets read.
- The user can produce an `NCCL_DEBUG=INFO` log — without it the transport is unknowable and
  the skill says so rather than guessing.
- Exact RDMA resource key + NCCL log format vary by device-plugin/NCCL version (hedged).

## Risk Assessment

- **R-1 — Bandwidth fabrication** (possible / high): quoting a hard busbw baseline would be
  false precision. Mitigation: the script never compares to a constant; every figure is
  tagged `[unverified vs baseline]`; an eval criterion enforces it.
- **R-2 — Resource-key drift** (likely / medium): `rdma/ib` may differ per device plugin.
  Mitigation: `[unverified]` tag + a `kubectl describe node` verification step.
- **R-3 — MPI Operator false positive** (possible / medium): flagging env vars "unset" when
  the MPI Operator manages them. Mitigation: the finding is explicitly hedged for that path.
- **R-4 — NCCL log format change** (possible / low): tokens are stable across versions but
  surrounding format shifts. Mitigation: key on stable tokens, fall back to `NET/*` counts.

## Traceability

| US | FR | Pain | Eval criterion |
|---|---|---|---|
| US-1 | FR-1,6 | CW-F1 | detects-net-socket-fallback, produces-actionable-verdict |
| US-2 | FR-2,3 | CW-F2, CW-F3 | gives-rdma-requests-and-limits-fix |
| US-3 | FR-1,6 | all | detects-net-socket-fallback |
| US-4 | FR-4 | CW-F4 | produces-actionable-verdict |
| US-5 | FR-5 | CW-F4 | no-hardcoded-bandwidth-baseline |

[cw]: https://docs.coreweave.com/docs/products/networking/hpc-interconnect/use-gpudirect-rdma
[nt]: https://github.com/coreweave/nccl-tests
[nccl]: https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/troubleshooting/networking_troubleshooting.html
[env]: https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html
