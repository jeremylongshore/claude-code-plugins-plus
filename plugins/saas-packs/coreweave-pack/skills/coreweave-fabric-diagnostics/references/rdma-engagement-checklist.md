# RDMA Engagement Checklist — the three conditions

_Last updated: 2026-07-02. Sourced from [CoreWeave "Use GPUDirect RDMA with
InfiniBand"][cw], the [coreweave/nccl-tests][nt] repo, and the [NVIDIA NCCL env][env] +
[networking troubleshooting][nccl] docs._

GPUDirect RDMA over InfiniBand engages only when **all three** of the conditions below
hold. Miss any one and NCCL **silently falls back to TCP** (`NET/Socket`) — the job runs
with no error at a fraction of the fabric's throughput. This is the checklist the skill's
`fabric-check.py` encodes.

## Condition 1 — the RDMA device is requested in BOTH requests AND limits

The Kubernetes pod must request the RDMA/InfiniBand device so the device plugin injects it
into the container. The common form is:

```yaml
resources:
  requests:
    nvidia.com/gpu: 8
    rdma/ib: 1
  limits:
    nvidia.com/gpu: 8
    rdma/ib: 1
```

- If `rdma/ib` is present in **only one** of the two blocks (a frequent copy-paste slip),
  or absent, the IB device is not guaranteed to be injected and NCCL finds no HCA →
  fallback. Put it in both.
- [unverified — the exact resource key depends on the installed RDMA device plugin
  (e.g. the k8s RDMA shared-device-plugin / SR-IOV / NVIDIA network-operator config). It
  may be `rdma/ib`, `rdma/hca_shared_devices_a`, or similar. Confirm the real key with
  `kubectl describe node` and read the Allocatable list, or `kubectl get node -o yaml`.]

**Verify:**

```bash
kubectl get pod "$POD" -o yaml | grep -A6 -E 'requests:|limits:'
kubectl describe node "$NODE" | grep -i rdma        # what the node actually advertises
```

## Condition 2 — the NCCL interface env vars are set

CoreWeave's documented multi-node values [[cw]]:

```bash
export NCCL_IB_HCA=ibp            # use the InfiniBand HCAs whose names start with "ibp"
export NCCL_SOCKET_IFNAME=eth0    # bootstrap/control-plane interface (NOT the data path)
```

- `NCCL_IB_HCA` selects which InfiniBand Host Channel Adapters NCCL uses; its format is
  `<hca>[:<port>]` with `^` to exclude and `=` for exact names [[env]]. On CoreWeave the
  HCAs are named `ibp...`, so `ibp` matches them all.
- `NCCL_SOCKET_IFNAME` names the IP interface used for **bootstrap/out-of-band**
  coordination; the high-speed data path still goes over IB. Pointing it at the wrong
  interface breaks rendezvous even when IB is healthy [[env]].
- **MPI Operator exception:** if you launch via the MPI Operator, it manages this network
  config and you generally do **not** set `NCCL_IB_HCA`/`NCCL_SOCKET_IFNAME` by hand [[nt]].
  The skill hedges its "env var unset" finding accordingly.
- Never ship `NCCL_IB_DISABLE=1` on an IB/RoCE cluster — it forces the socket fallback by
  design [[env]].

## Condition 3 — NCCL_DEBUG=INFO confirms NET/IB

The only way to _know_ RDMA engaged (rather than assume it) is to read the transport NCCL
actually chose:

```bash
NCCL_DEBUG=INFO <your training launch> 2>&1 | tee nccl-debug.log
grep -E 'Using network|NET/IB|NET/Socket|GPU Direct RDMA' nccl-debug.log
```

- **Good:** `Using network IB`, `NET/IB : ...`, and ideally `NET/IB : GPU Direct RDMA
  Enabled for GPU ...` (or a channel line `via NET/IB/0/GDRDMA`).
- **Bad (fallback):** `Using network Socket` / `NET/Socket : Using [0]eth0...`.
- **GDR staging warning:** `NET/IB` without a `GPU Direct RDMA Enabled` line can mean
  traffic is staging through host memory (nvidia-peermem not loaded) — engaged but not at
  full GDR speed [[nccl]].

See [`nccl-debug-reading.md`](nccl-debug-reading.md) for line-by-line interpretation.

## Why the fallback is silent (and expensive)

NCCL is designed to _degrade rather than fail_: if it cannot bring up the IB transport it
uses TCP sockets so the job still completes. For a single-node job that is fine; for a
multi-node collective it means every all-reduce crosses the ~Ethernet control plane instead
of the InfiniBand fabric, and end-to-end throughput can drop **5-20x** [[nccl]] with the
GPUs still billing at full rate. Nothing in the default job output flags it — which is why
an explicit `NCCL_DEBUG=INFO` transport check belongs in every multi-node run's smoke test.

[cw]: https://docs.coreweave.com/docs/products/networking/hpc-interconnect/use-gpudirect-rdma
[nt]: https://github.com/coreweave/nccl-tests
[nccl]: https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/troubleshooting/networking_troubleshooting.html
[env]: https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html
