# Vast.ai Skill Pack

> Claude Code skill pack for Vast.ai GPU cloud marketplace integration (24 skills)

## Installation

```bash
/plugin install vastai-pack@claude-code-plugins-plus
```

## About Vast.ai

[Vast.ai](https://vast.ai) is a GPU cloud marketplace where individual hosts and data centers list GPU machines at prices 50-90% below hyperscaler providers. Common use cases: ML training, inference, rendering, and any GPU-accelerated workload where cost efficiency matters.

**Key facts:**
- REST API at `cloud.vast.ai/api/v0` + CLI via `pip install vastai`
- Pricing: RTX 4090 ~$0.15-0.30/hr, A100 ~$1.00-2.00/hr, H100 ~$2.50-4.00/hr
- Instance types: on-demand and interruptible (spot)
- Access: SSH + Docker containers on rented GPU hardware

## Skills Included

### Standard Skills (S01-S12)
| Skill | Description |
|-------|-------------|
| `vastai-install-auth` | Install CLI, configure API key, build Python client |
| `vastai-hello-world` | Rent first GPU instance, run PyTorch workload, destroy |
| `vastai-local-dev-loop` | Mock API, test Docker images locally, connection testing |
| `vastai-sdk-patterns` | Typed queries, context-managed lifecycle, offer scoring |
| `vastai-core-workflow-a` | Search, provision, execute job, collect artifacts, destroy |
| `vastai-core-workflow-b` | Multi-instance orchestration, spot recovery, cost analysis |
| `vastai-common-errors` | API errors, instance failures, SSH issues, CUDA problems |
| `vastai-debug-bundle` | Account diagnostics, instance logs, GPU health, nvidia-smi |
| `vastai-rate-limits` | Rate-limited client, adaptive polling, request optimization |
| `vastai-security-basics` | API key management, SSH hardening, data cleanup |
| `vastai-prod-checklist` | Production readiness audit with verification script |
| `vastai-upgrade-migration` | CLI upgrades, CUDA migration, Docker image updates |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `vastai-ci-integration` | GitHub Actions GPU testing with budget controls |
| `vastai-deploy-integration` | Automated deployment scripts, Docker optimization |
| `vastai-webhooks-events` | Instance lifecycle polling, auto-recovery handlers |
| `vastai-performance-tuning` | dlperf scoring, DataLoader tuning, batch sizing |
| `vastai-cost-tuning` | GPU cost-efficiency, spot vs on-demand, auto-destroy |
| `vastai-reference-architecture` | Three-tier architecture, checkpoint manager |

### Flagship Skills (F19-F24)
| Skill | Description |
|-------|-------------|
| `vastai-multi-env-setup` | Dev/staging/prod API keys, GPU whitelists, budgets |
| `vastai-observability` | Metrics collection, GPU alerts, Prometheus exporter |
| `vastai-incident-runbook` | Triage scripts, spot recovery, billing emergency stop |
| `vastai-data-handling` | Encrypted transfer, cloud checkpoints, secure cleanup |
| `vastai-enterprise-rbac` | Team budgets, policy enforcement, audit logging |
| `vastai-migration-deep-dive` | AWS/GCP to Vast.ai, cost comparison, Docker adaptation |

## Quick Start

```bash
# Install CLI
pip install vastai

# Configure API key
vastai set api-key YOUR_KEY_FROM_CLOUD_VAST_AI

# Search for cheap GPUs
vastai search offers 'num_gpus=1 gpu_ram>=24 reliability>0.95' --order dph_total --limit 5

# Rent an instance
vastai create instance OFFER_ID --image pytorch/pytorch:2.2.0-cuda12.1-cudnn8-runtime --disk 20

# Connect and verify
ssh -p PORT root@HOST "nvidia-smi"

# IMPORTANT: Destroy when done (stops billing)
vastai destroy instance INSTANCE_ID
```

## Resources

- [Vast.ai Documentation](https://docs.vast.ai)
- [REST API Reference](https://vast.ai/developers/api)
- [CLI GitHub](https://github.com/vast-ai/vast-cli)
- [Search & Filter](https://docs.vast.ai/search-and-filter-gpu-offers)

## License

MIT
