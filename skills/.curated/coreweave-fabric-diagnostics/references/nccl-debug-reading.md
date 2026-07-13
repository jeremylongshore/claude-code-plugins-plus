# Reading NCCL_DEBUG=INFO — NET/IB vs NET/Socket

_Last updated: 2026-07-02. Sourced from the [NVIDIA NCCL networking-troubleshooting][nccl]
and [env-variables][env] docs and [coreweave/nccl-tests][nt]. Exact log strings vary by
NCCL version; the tokens below (`NET/IB`, `NET/Socket`, `Using network`, `GPU Direct RDMA
Enabled`) are the stable signals the skill greps for._

`NCCL_DEBUG=INFO` makes NCCL print, at startup, exactly which network transport it selected.
That one decision — InfiniBand or TCP — is the whole ballgame for multi-node speed, and it
is the thing operators most often assume rather than verify.

## The decisive line

NCCL prints a single line naming the chosen network:

```text
NCCL INFO Using network IB          # GOOD  — InfiniBand verbs transport
NCCL INFO Using network Socket      # BAD   — TCP sockets (the fallback)
```

`fabric-check.py` treats `Using network Socket` / `Using network IB` as authoritative when
present. If that line is absent (truncated paste), it falls back to counting `NET/IB` vs
`NET/Socket` occurrences.

## The supporting lines

```text
NCCL INFO NET/IB : Using [0]ibp0:1/IB [1]ibp1:1/IB ...      # IB HCAs bound
NCCL INFO NET/IB : GPU Direct RDMA Enabled for GPU 0000:...  # GDR confirmed (best)
NCCL INFO Channel 00/0 : 0[0] -> 1[0] [send] via NET/IB/0/GDRDMA
```

versus the fallback:

```text
NCCL INFO NET/Socket : Using [0]eth0:10.0.0.4    # TCP path over the control-plane NIC
NCCL INFO Using network Socket
```

- **`GPU Direct RDMA Enabled` / `/GDRDMA`** is the strongest signal — the NIC DMAs straight
  to/from GPU memory. Its absence with `NET/IB` present suggests staging through host memory
  (nvidia-peermem not loaded), which is engaged-but-slower [[nccl]].
- **Both `NET/IB` and `NET/Socket` present** = partial fallback: some rails/nodes are on IB,
  some dropped to sockets. The collective is gated by the slow path — treat as degraded and
  find the node/rail that fell back.

## Warnings that explain a fallback

When NCCL _tried_ IB and failed, it says so before falling back:

```text
NCCL WARN Call to ibv_create_qp failed
NCCL WARN Call to ibv_reg_mr failed
NCCL WARN NET/IB : Got completion with error ...
```

These mean the IB device was visible but the verbs layer failed (driver/OFED, memory
registration, or a QP limit) — a different fix than "the device was never injected." The
skill flags `ib_attempt_failed_in_log` when it sees a `NCCL WARN` tied to IB/`ibv_`.

## Transport-control env vars (for reference)

| Variable | Effect | Note |
|---|---|---|
| `NCCL_IB_DISABLE` | `1` disables IB/RoCE → forces IP sockets | Must be `0` (default) on an IB/RoCE cluster [[env]] |
| `NCCL_NET_GDR_LEVEL` | Controls when GPU Direct RDMA is used by NIC↔GPU distance (`LOC`…`SYS`) | `SYS` enables GDR even across NUMA; `LOC` disables it [[env]] |
| `NCCL_IB_HCA` | Which IB HCAs NCCL uses (`ibp` on CoreWeave) | Format `<hca>[:<port>]`, `^` exclude, `=` exact [[env]] |
| `NCCL_SOCKET_IFNAME` | Bootstrap/control interface (`eth0`) | Data path stays on IB; this is out-of-band only [[env]] |

## What the skill's checker keys on

1. `Using network Socket` (case-insensitive) → transport `Socket`, `rdma_engaged: no`.
2. `Using network IB` → transport `IB`; `rdma_engaged: yes` (GDR-confirmed if a
   `GPU Direct RDMA Enabled` / `GDRDMA` token is present).
3. Both tokens without a decisive line → `mixed` (partial fallback).
4. Neither → `unknown` (re-run with `NCCL_DEBUG=INFO`).

[nccl]: https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/troubleshooting/networking_troubleshooting.html
[env]: https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html
[nt]: https://github.com/coreweave/nccl-tests
