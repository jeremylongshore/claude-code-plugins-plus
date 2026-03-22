# CAST AI Skill Pack

> 18 production-grade Claude Code skills for Kubernetes cost optimization with CAST AI

## What Is CAST AI?

[CAST AI](https://cast.ai) is an all-in-one Kubernetes cost optimization, autoscaling, and security platform. It connects to EKS, GKE, and AKS clusters to:

- **Autoscale nodes** by adding right-sized instances and removing underutilized ones
- **Use spot instances** with automatic diversity and fallback to on-demand
- **Right-size workloads** via pod-level resource recommendations (Workload Autoscaler)
- **Hibernate clusters** on schedule for dev/staging environments
- **Scan for security issues** with the Kvisor runtime agent

Typical savings: 50-70% on cloud compute costs. The platform uses a REST API at `api.cast.ai` with `X-API-Key` header authentication and provides a Terraform provider for infrastructure-as-code management.

This skill pack provides real API calls, Helm commands, and Terraform configurations for every stage of CAST AI adoption.

## Installation

```bash
/plugin install castai-pack@claude-code-plugins-plus
```

## Skills Included

### Getting Started (S01-S04)

| Skill | Description |
|-------|-------------|
| `castai-install-auth` | Helm agent install, API key setup, Terraform provider config |
| `castai-hello-world` | First API calls: list clusters, savings report, node inventory |
| `castai-local-dev-loop` | Dev cluster policies, Terraform plan-apply loop, savings scripts |
| `castai-sdk-patterns` | TypeScript/Python REST API client wrappers with retry and types |

### Core Workflows (S05-S08)

| Skill | Description |
|-------|-------------|
| `castai-core-workflow-a` | Configure autoscaler policies, spot instances, node templates |
| `castai-core-workflow-b` | Workload Autoscaler: pod right-sizing, annotations, scaling policies |
| `castai-common-errors` | Agent CrashLoop, nodes not scaling, spot fallback, evictor issues |
| `castai-debug-bundle` | Collect agent logs, Helm releases, policies, and events for support |

### Operations (S09-S12)

| Skill | Description |
|-------|-------------|
| `castai-rate-limits` | API rate limit detection, exponential backoff, request queuing |
| `castai-security-basics` | API key rotation, RBAC audit, Kvisor agent, network policies |
| `castai-prod-checklist` | Phase 1 to Phase 2 go-live checklist with validation commands |
| `castai-upgrade-migration` | Helm chart upgrades, Terraform provider updates, rollback procedures |

### Pro Skills (P13-P18)

| Skill | Description |
|-------|-------------|
| `castai-ci-integration` | GitHub Actions savings gate, Terraform plan validation in CI |
| `castai-deploy-integration` | Multi-cloud Terraform modules for EKS, GKE, and AKS onboarding |
| `castai-webhooks-events` | Event notifications, Slack integration, audit log API, CronJob summaries |
| `castai-performance-tuning` | Headroom config, instance family selection, API caching for dashboards |
| `castai-cost-tuning` | Spot strategies, right-sizing analysis, cluster hibernation, cost tracking |
| `castai-reference-architecture` | Multi-cluster Terraform module structure with per-environment policies |

## Quick Start

### 1. Install the Pack

```bash
/plugin install castai-pack@claude-code-plugins-plus
```

### 2. Get Your API Key

Sign up at [console.cast.ai](https://console.cast.ai), navigate to **API > API Access Keys**, and create a Full Access key.

### 3. Connect Your First Cluster

```bash
export CASTAI_API_KEY="your-key"

# Add Helm repo
helm repo add castai-helm https://castai.github.io/helm-charts
helm repo update

# Install monitoring agent
helm upgrade --install castai-agent castai-helm/castai-agent \
  -n castai-agent --create-namespace \
  --set apiKey="${CASTAI_API_KEY}" \
  --set provider="eks"
```

### 4. Check Your Savings

```bash
export CASTAI_CLUSTER_ID="your-cluster-id"

curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
  "https://api.cast.ai/v1/kubernetes/clusters/${CASTAI_CLUSTER_ID}/savings" \
  | jq '{monthly: .monthlySavings, percent: .savingsPercentage}'
```

### 5. Enable Autoscaling

Follow `castai-core-workflow-a` to configure autoscaler policies and start saving.

## Key CAST AI Links

- [CAST AI Console](https://console.cast.ai) -- cluster management dashboard
- [CAST AI Docs](https://docs.cast.ai/docs/getting-started) -- getting started guide
- [API Reference](https://api.cast.ai/v1/spec/openapi.json) -- OpenAPI spec
- [Terraform Provider](https://registry.terraform.io/providers/castai/castai/latest/docs) -- IaC modules
- [Helm Charts](https://docs.cast.ai/docs/helm-charts) -- agent and component charts
- [GitHub](https://github.com/castai) -- open-source components
- [CAST AI Status](https://status.cast.ai) -- platform status page

## License

MIT
