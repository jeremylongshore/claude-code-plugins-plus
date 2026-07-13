# Xid → Triage Action Table

**Last verified: 2026-07-02.** Kept in lockstep with `scripts/triage.py` `XID_TABLE`.

**Primary source:** NVIDIA Xid Errors reference —
<https://docs.nvidia.com/deploy/xid-errors/> (the "Xid Error Listing" and
"Working with Xid Errors" sections). Row-remapper semantics:
NVIDIA GPU Memory Error Management —
<https://docs.nvidia.com/deploy/a100-gpu-mem-error-mgmt/index.html>.
CoreWeave node lifecycle / cordon behavior: see `cordon-rules.md`.

> This table is a decision aid, not a substitute for the vendor catalog. When an
> Xid is not listed here, `triage.py` returns a conservative drain + GPU-reset
> default and flags it `[unverified]`.

## The six actions

| Action | Meaning | Blast radius |
|---|---|---|
| `reschedule` | Restart the job; the GPU/node is healthy. | One job restart. |
| `reset-gpu` | Drain + GPU reset; in-flight work on that GPU is suspect. | Jobs sharing the GPU. |
| `reboot-node` | Bare-metal reboot; the card is gone until then. | The whole node's jobs. |
| `rma` | Terminal hardware fault; replace the card. | Node out until swapped. |
| `watch` | Correctable / trending; not yet actionable. | None yet. |
| `app-bug-not-hardware` | The application faulted, not the GPU. Do NOT RMA. | The buggy job only. |

## The table

| Xid | Name (NVIDIA catalog) | Class | Severity | Action | One-line why |
|---:|---|---|---|---|---|
| 13 | Graphics/Compute Engine Exception | App | low | `app-bug-not-hardware` | Illegal access / bad kernel launch — an app bug, not hardware. |
| 31 | GPU memory page fault (MMU fault) | App | low | `app-bug-not-hardware` | Out-of-bounds memory access by the app; run compute-sanitizer. |
| 43 | GPU stopped processing | App | low | `app-bug-not-hardware` | Software-induced channel fault; not hardware. |
| 45 | Preemptive cleanup / robust channel recovery | App | low | `app-bug-not-hardware` | Teardown after a kill/preempt — a symptom, look for the preceding Xid. |
| 48 | Double-Bit ECC error (DBE) | HW | critical | `reset-gpu` | Uncorrectable ECC — reset; a row-remap should follow (RMA if it fails). |
| 63 | ECC page retirement / row-remap recorded | HW | high | `reset-gpu` | Routine remap; applies on reset **unless** the remap failed → RMA. |
| 64 | ECC row-remapper recording **failure** | HW | critical | `rma` | The sparing hardware itself failed — terminal, replace the card. |
| 74 | NVLink error | HW | high | `reset-gpu` | NVLink/NVSwitch error; reset the domain, escalate if it recurs. |
| 79 | GPU has fallen off the bus | HW | critical | `reboot-node` | Off the PCIe bus, unreachable until a bare-metal reboot. |
| 92 | High single-bit ECC (SBE) rate | HW | medium | `watch` | Correctable + self-healing; act only if it escalates to DBE/remap-failure. |
| 94 | Contained ECC error | HW | high | `reschedule` | **CONTAINED** to the app context — node is fine, just restart the job. |
| 95 | Uncontained ECC error | HW | critical | `reset-gpu` | **UNCONTAINED** — everything the GPU touched is suspect; drain + reset. |
| 119 | GSP RPC timeout | HW | high | `reset-gpu` | GSP fault; a GPU reset usually clears it. |
| 120 | GSP error | HW | high | `reset-gpu` | GSP fault; a GPU reset usually clears it, reboot if not. |

## The headline distinction: Xid 94 vs Xid 95

This is the single most valuable bit in the table and the reason the skill exists.

- **Xid 94 — CONTAINED.** The GPU's error-containment isolated the fault to the
  faulting application's context. The hardware self-protected: the node and GPU
  are healthy. The correct move is the cheapest one — **reschedule the failed
  rank**. Resetting or RMAing here wastes GPU-hours and drains a healthy node.
- **Xid 95 — UNCONTAINED.** The GPU could **not** isolate the fault. Any context
  that shared the GPU is now suspect, including collectives that read poisoned
  memory. The correct move is **drain + GPU reset**, and re-run every job that
  shared the card. Treating a 95 like a 94 (just restarting) risks silently
  corrupt training state.

Getting this one bit wrong is the difference between a 30-second reschedule and a
multi-day run that trained on corrupt gradients. `triage.py` never lets the LLM
eyeball it — the code decides.

## App-side Xids: do NOT RMA

Xid **13 / 31 / 43 / 45** are application/CUDA-side faults (illegal memory
access, bad kernel, channel teardown after a kill). RMAing a card for these is a
false positive that pulls healthy hardware out of the fleet and never fixes the
job — the fix is in the application. `triage.py` classes these
`app-bug-not-hardware` and points at compute-sanitizer, not an RMA ticket.

## Escalation ladder (correctable → terminal)

`watch` (Xid 92 SBE trend) → `reset-gpu` (Xid 48 DBE, Xid 63 remap pending) →
`rma` (Xid 64 / remap-failure). A single SBE is noise; a rising SBE rate is a
watch item; a DBE forces a reset + remap; a remap **failure** is terminal.

> **[unverified]** CoreWeave's exact automatic-RMA thresholds — how many SBEs, or
> how few remaining remap banks, trip an automatic card replacement — are **not
> publicly published**. The ladder above is the NVIDIA-documented physics;
> confirm the operator-side auto-RMA trigger with CoreWeave support.
