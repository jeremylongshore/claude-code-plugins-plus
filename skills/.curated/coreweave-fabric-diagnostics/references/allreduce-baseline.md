# all_reduce_perf — reading busbw, and why the baseline is never hardcoded

_Last updated: 2026-07-02. Sourced from [coreweave/nccl-tests][nt] and the [NVIDIA NCCL
troubleshooting][nccl] docs. Every absolute GB/s figure here is illustrative and tagged
[unverified vs baseline]._

`all_reduce_perf` (from CoreWeave's [nccl-tests][nt]) is the ground-truth fabric benchmark:
it runs an all-reduce across the GPUs and reports achieved bandwidth. It is how you tell
"RDMA is engaged but slow" apart from "RDMA is engaged and healthy."

## The columns

```text
#       size         count      type    redop     time   algbw   busbw
   536870912     134217728     float     sum    1234.5   434.8   815.2
```

- **`algbw`** (algorithm bandwidth) — data size ÷ time. What your program moves.
- **`busbw`** (bus bandwidth) — `algbw` scaled by the collective's communication factor
  (`2·(n-1)/n` for ring all-reduce). **This is the number to compare across GPU counts**,
  because it normalizes for the algorithm and approximates the per-link fabric rate.
- nccl-tests also prints a summary line, e.g. `# Avg bus bandwidth : 373.187`
  `[unverified vs baseline — this specific figure is from a particular SHARP-enabled H100
  run in the nccl-tests README, not a target for your cluster]`.

## The rule: compare against CoreWeave's manifest baseline, not a constant

**Do not hardcode a pass/fail busbw number.** The expected busbw for a healthy fabric
depends on:

- **GPU type** (H100 vs H200 vs GB200/NVL72),
- **GPU / node count** (per-link vs aggregate, and whether it crosses the spine),
- **NCCL version** (algorithms and defaults change release to release),
- **SHARP** (in-network reduction on the IB switches lifts effective busbw substantially),
- **message size** (small messages are latency-bound; busbw only approaches peak at large
  sizes).

The right baseline is **CoreWeave's own published nccl-tests manifest result for your exact
GPU count + image/NCCL version** [[nt]] — run the same manifest and compare like-for-like.
The skill's `fabric-check.py` therefore **echoes** the observed `Avg bus bandwidth` tagged
`[unverified vs baseline]` and never verdicts pass/fail on an absolute number. What it _can_
say deterministically: a `NET/Socket` transport with a low busbw corroborates the TCP
fallback; the transport call is the reliable signal, the busbw is the corroboration.

## Orders of magnitude (directional only)

The reason fallback is so costly is the raw interconnect gap: an InfiniBand fabric (e.g.
NDR-class, hundreds of Gb/s per port) versus the Ethernet control plane it falls back to.
When NCCL drops to `NET/Socket`, measured busbw typically collapses by **5-20x** [[nccl]].
`[unverified — the exact multiplier depends on message size, GPU count, and model; treat
5-20x as a directional range, benchmark your own before quoting a figure.]`

## How to run it (for reference)

```bash
# via MPI Operator / mpirun across the nodes, using CoreWeave's nccl-tests image
mpirun ... all_reduce_perf -b 8 -e 8G -f 2 -g 1
```

Then compare the reported `busbw` (large-size rows and the Avg line) against the CoreWeave
manifest baseline for the same topology. A healthy run tracks the baseline; a run that
tracks ~1/10th of it — with `NET/Socket` in the NCCL log — is the fallback this skill
exists to catch.

[nt]: https://github.com/coreweave/nccl-tests
[nccl]: https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/troubleshooting/networking_troubleshooting.html
