# GPU Right-Sizing Decision Table

_Last updated: 2026-07-02. Rate card is a dated snapshot of [coreweave.com/pricing][pr]
(North America, on-demand). **Verify against your contract before acting** — rates and
availability change._

CoreWeave publishes no price metric, so the ranker is fed these rates explicitly. Prices
below are quoted per **8-GPU node** on the pricing page; the per-GPU-hour column is
derived by dividing by 8 (GH200 is sold per single GPU).

## Rate card (on-demand, North America)

| GPU | Node price/hr | Per GPU/hr (derived) | Best for |
|-----|--------------:|---------------------:|----------|
| L40 (8×) | $10.00 | ~$1.25 | Image gen, light inference |
| A100 (8×) | $21.60 | ~$2.70 | Mid-size inference, dev |
| L40S (8×) | $18.00 | ~$2.25 | **7B–30B inference sweet spot** |
| HGX H100 (8×) | $49.24 | ~$6.16 | Training, high-throughput / long-context inference |
| HGX H200 (8×) | $50.44 | ~$6.31 | Training, largest-context inference |
| GH200 (1×) | $6.50 | $6.50 | Grace-Hopper, large unified memory |

Committed use: **up to 60% off** on-demand ([pr]) — take-or-pay (see
[gpu-cost-leak-categories.md](gpu-cost-leak-categories.md) Category 1/4).

## The right-sizing decision (directional)

> **These $/token conclusions are directional and third-party.** They swing by model,
> batch size, sequence length, quantization, framework, and month. Treat as a *starting
> hypothesis to benchmark on your own traffic*, not a guarantee. `[unverified — no
> single authoritative CoreWeave $/token benchmark exists; validate per workload.]`

| Model size (inference) | Start with | Why |
|---|---|---|
| ≤ 7B | L40 or L40S | Fits comfortably; H100 is idle silicon at rack rate |
| 7B–30B | **L40S** | Often the best $/token; H100/H200 over-provisioned here |
| 30B–70B (quantized) | A100 80GB or L40S ×N | AWQ/GPTQ/FP8 can fit one or few GPUs |
| 70B+ / long-context / high-QPS | H100 / H200 | Memory bandwidth + NVLink actually earn the premium |
| Training / multi-node | H100 / H200 | NVLink + InfiniBand interconnect is the point |

**The core leak:** running 7B–30B inference on H100/H200 pays ~$6.16–$6.31/GPU-hr for
work an L40S does at ~$2.25/GPU-hr. The re-price delta is exact rate-card math; whether
L40S sustains your throughput target is the part to benchmark (hence the leak is tagged
**Estimated**, never Confirmed).

## The FP8 rule (hard constraint, not directional)

FP8 inference and training run on **Hopper (H100/H200) and Ada (L40/L40S)** — the
4th-gen Tensor Cores with native FP8. **Ampere (A100) has no FP8 path.**

- Re-hosting an FP8 workload **onto A100 is invalid** — it silently falls back to a wider
  dtype (loses the FP8 memory/throughput win) or fails to load. Right-size FP8 inference
  to **L40S**, not A100.
- Moving an FP8 workload H100 → L40S is valid on the FP8 axis (both Ada/Hopper support
  FP8); benchmark for throughput before committing.
- BF16/FP16 workloads have no such constraint and can target A100 freely.

## Detection corroboration

- `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` chronically low on a Hopper node → the workload is
  not saturating the tensor cores you are paying the premium for → strong re-host signal.
- `DCGM_FI_DEV_FB_USED` well below the card's memory → the model does not need the big
  GPU's capacity → candidate for a smaller card.

[pr]: https://www.coreweave.com/pricing
