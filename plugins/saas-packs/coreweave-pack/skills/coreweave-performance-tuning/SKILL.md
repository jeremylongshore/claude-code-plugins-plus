---
name: coreweave-performance-tuning
description: |
  Optimize CoreWeave GPU inference latency and throughput.
  Use when reducing inference latency, maximizing GPU utilization,
  or tuning batch sizes and concurrency.
  Trigger with phrases like "coreweave performance", "coreweave latency",
  "coreweave throughput", "optimize coreweave inference".
allowed-tools: Read, Write, Edit, Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, gpu-cloud, kubernetes, inference, coreweave]
compatible-with: claude-code
---

# CoreWeave Performance Tuning

## GPU Selection by Workload

| Workload | Recommended GPU | Why |
|----------|----------------|-----|
| LLM inference (7-13B) | A100 80GB | Good balance of memory and cost |
| LLM inference (70B+) | 8xH100 | NVLink for tensor parallelism |
| Image generation | L40 | Good for diffusion models |
| Training (large models) | 8xH100 SXM5 | Fastest interconnect |
| Batch processing | A100 40GB | Cost-effective |

## Inference Optimization

```yaml
# Continuous batching with vLLM
containers:
  - name: vllm
    args:
      - "--model=meta-llama/Llama-3.1-8B-Instruct"
      - "--max-num-batched-tokens=8192"
      - "--max-num-seqs=256"
      - "--gpu-memory-utilization=0.90"
      - "--enable-prefix-caching"
      - "--dtype=float16"
```

## Autoscaling Tuning

```yaml
# HPA based on GPU utilization
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: inference-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: inference-server
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Pods
      pods:
        metric:
          name: DCGM_FI_DEV_GPU_UTIL
        target:
          type: AverageValue
          averageValue: "70"
```

## Performance Benchmarks

| Metric | A100-80GB | H100-80GB |
|--------|-----------|-----------|
| Llama-8B tokens/sec | ~2,000 | ~4,500 |
| Llama-70B tokens/sec | ~200 (4x) | ~500 (4x) |
| Cold start (vLLM) | 30-60s | 20-40s |

## Resources

- [CoreWeave Inference](https://www.coreweave.com/solutions/ai-inference)
- [vLLM Documentation](https://docs.vllm.ai)

## Next Steps

For cost optimization, see `coreweave-cost-tuning`.
