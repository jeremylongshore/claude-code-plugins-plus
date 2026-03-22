---
name: coreweave-cost-tuning
description: |
  Optimize CoreWeave GPU cloud costs with right-sizing and scheduling.
  Use when reducing GPU spend, selecting cost-effective instances,
  or implementing scale-to-zero for dev workloads.
  Trigger with phrases like "coreweave cost", "coreweave pricing",
  "reduce coreweave spend", "coreweave budget".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, gpu-cloud, kubernetes, inference, coreweave]
compatible-with: claude-code
---

# CoreWeave Cost Tuning

## GPU Pricing Reference (approximate)

| GPU | Per GPU/hour | Best For |
|-----|-------------|----------|
| A100 40GB PCIe | ~$1.50 | Development, smaller models |
| A100 80GB PCIe | ~$2.21 | Production inference |
| H100 80GB PCIe | ~$4.76 | High-throughput inference |
| H100 SXM5 (8x) | ~$6.15/GPU | Training, multi-GPU |
| L40 | ~$1.10 | Image generation, light inference |

## Cost Optimization Strategies

### Scale-to-Zero for Dev/Staging
```yaml
autoscaling.knative.dev/minScale: "0"
autoscaling.knative.dev/scaleDownDelay: "5m"
```

### Right-Size GPU Selection
```python
def recommend_gpu(model_size_b: float, inference_only: bool = True) -> str:
    if model_size_b <= 7:
        return "L40" if inference_only else "A100_PCIE_80GB"
    elif model_size_b <= 13:
        return "A100_PCIE_80GB"
    elif model_size_b <= 70:
        return "A100_PCIE_80GB (4x tensor parallel)"
    else:
        return "H100_SXM5 (8x tensor parallel)"
```

### Quantization to Use Smaller GPUs
Use AWQ or GPTQ quantization to fit larger models on smaller GPUs:
```bash
# 70B model at 4-bit fits on single A100-80GB instead of 4x
vllm serve meta-llama/Llama-3.1-70B-Instruct-AWQ --quantization awq
```

## Resources

- [CoreWeave Pricing](https://www.coreweave.com/pricing)
- [CoreWeave GPU Instances](https://docs.coreweave.com/docs/platform/instances/gpu-instances)

## Next Steps

For architecture patterns, see `coreweave-reference-architecture`.
