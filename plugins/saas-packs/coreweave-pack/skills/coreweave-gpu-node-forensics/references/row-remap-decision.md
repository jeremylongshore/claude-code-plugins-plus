# Row-Remap Decision: routine vs terminal

**Last verified: 2026-07-02.**

**Primary source:** NVIDIA GPU Memory Error Management (row remapping on
Ampere/Hopper) — <https://docs.nvidia.com/deploy/a100-gpu-mem-error-mgmt/index.html>.
Xid semantics: <https://docs.nvidia.com/deploy/xid-errors/>.

Ampere and later GPUs replace the legacy dynamic page-retirement scheme with
**row remapping**: when a memory row goes bad, the GPU swaps in a spare row from a
reserved bank. This is self-healing hardware — most row-remap events are routine.
The one that is **not** routine is a remap **failure**, and that single field is
the difference between "reset and move on" and "RMA the card."

## Read the remapper state

```bash
nvidia-smi -q -d ROW_REMAPPER
```

Relevant fields:

```
    Remapping Failure Occurred          : No        # <- the terminal flag
    Pending                             : Yes       # <- a remap is queued
    Correctable Error                   : 12
    Uncorrectable Error                 : 0
    Histogram
        Max                             : 639 bank(s)
        High                            : 0 bank(s)
        ...
        None                            : 1 bank(s)  # <- spare banks nearly exhausted
```

## The decision

| `Remapping Failure Occurred` | `Pending` | Verdict | Action |
|---|---|---|---|
| **Yes** | (any) | **Terminal** — the sparing hardware itself failed. | `rma` |
| No | **Yes** | **Routine** — a remap is queued and applies on the next GPU reset. | `reset-gpu` |
| No | No | Remap already recorded and applied; monitor remaining banks. | `watch` |

`triage.py` applies exactly this precedence in `apply_remap_override()`:
`Remapping Failure Occurred: Yes` **overrides everything** (even a base verdict
of reset) straight to `rma`; a bare `Pending: Yes` with no failure yields
`reset-gpu`. The failure flag is authoritative because it means the GPU tried to
self-heal and physically could not.

## Why "Pending: Yes" is good news, not bad

A pending remap means the GPU **detected** a bad row and **has a spare to swap in**
— it just needs a reset to activate it. That is the memory-error subsystem working
as designed. Draining the job and resetting the GPU applies the remap and the card
returns to service. Do not RMA a card whose only sin is a pending remap.

## Xid 48 / 63 / 64 in remap terms

- **Xid 48 (DBE)** — an uncorrectable double-bit error triggered the remap flow.
  Reset the GPU; a remap should follow. If it fails → RMA.
- **Xid 63** — a row-remap (or legacy page retirement) was **recorded**. Routine;
  applies on reset. Check the remapper state to confirm no failure.
- **Xid 64** — the row-remapper **recording failed**. This is the failure case in
  Xid form; it maps straight to `rma`.

## When the banks run out

If the remap histogram shows the spare banks nearly exhausted (few/no remaining
banks) the card is running out of self-healing capacity even without a failure
flag. Treat that as an escalation toward RMA.

> **[unverified]** The exact remaining-bank count at which CoreWeave auto-flags a
> card for RMA is **not publicly published**. NVIDIA documents the mechanism, not
> a provider's operational trigger — confirm the threshold with CoreWeave support.
