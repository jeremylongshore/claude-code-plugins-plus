---
name: coreweave-reference-architecture
description: |
  Reference architecture for CoreWeave GPU cloud deployments.
  Use when designing ML infrastructure, planning multi-model serving,
  or establishing CoreWeave deployment standards.
  Trigger with phrases like "coreweave architecture", "coreweave design",
  "coreweave infrastructure", "coreweave best practices".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, gpu-cloud, kubernetes, inference, coreweave]
compatible-with: claude-code
---

# CoreWeave Reference Architecture

## Architecture Diagram

```
                    ┌─────────────────────┐
                    │   Load Balancer     │
                    │   (Ingress/LB)      │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
     ┌────────▼──────┐ ┌──────▼────────┐ ┌─────▼───────┐
     │ Model A       │ │ Model B       │ │ Model C     │
     │ (vLLM, A100)  │ │ (TGI, H100)  │ │ (SD, L40)   │
     │ 2 replicas    │ │ 1 replica     │ │ 3 replicas  │
     └───────────────┘ └───────────────┘ └─────────────┘
              │                │                │
     ┌────────▼────────────────▼────────────────▼───────┐
     │              Shared Storage (PVC)                │
     │         Models / Checkpoints / Data              │
     └──────────────────────────────────────────────────┘
```

## Project Structure

```
ml-platform/
├── k8s/
│   ├── base/                    # Shared templates
│   ├── models/
│   │   ├── llama-8b/           # Per-model manifests
│   │   ├── llama-70b/
│   │   └── stable-diffusion/
│   └── infra/
│       ├── storage.yaml         # PVCs
│       ├── secrets.yaml         # Model tokens
│       └── monitoring.yaml      # Prometheus rules
├── containers/
│   ├── vllm/Dockerfile
│   └── custom-server/Dockerfile
├── scripts/
│   ├── deploy.sh
│   └── benchmark.sh
└── monitoring/
    ├── grafana-dashboards/
    └── alert-rules.yaml
```

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Serving framework | vLLM | Continuous batching, PagedAttention |
| GPU type (production) | A100 80GB | Best price/performance for inference |
| Storage | Shared PVC (SSD) | Fast model loading across replicas |
| Autoscaling | KServe + Knative | Native scale-to-zero support |
| Container registry | GHCR | GitHub integration, free for public |

## Resources

- [CoreWeave Documentation](https://docs.coreweave.com)
- [CoreWeave Examples](https://github.com/coreweave/kubernetes-cloud)

## Next Steps

For multi-environment setup, see `coreweave-multi-env-setup`.
