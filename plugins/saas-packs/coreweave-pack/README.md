# CoreWeave Skill Pack

> 24 production-grade Claude Code skills for GPU cloud computing with CoreWeave Kubernetes Service

## What Is CoreWeave?

[CoreWeave](https://www.coreweave.com) is a specialized GPU cloud platform built for AI/ML workloads. CoreWeave Kubernetes Service (CKS) runs Kubernetes directly on bare-metal GPU nodes -- no hypervisor, no VMs. The platform provides:

- **Bare-metal GPU nodes** with A100, H100, L40, and GH200 GPUs
- **KServe integration** for serverless inference with scale-to-zero
- **Multi-node training** with NVLink and InfiniBand interconnect
- **Shared storage** (HDD, SSD, NVMe) via Kubernetes PVCs
- **DCGM metrics** for GPU utilization monitoring out of the box

Access is via standard kubectl with CoreWeave-issued kubeconfig. GPU scheduling uses node affinity with `gpu.nvidia.com/class` labels. Typical cost savings: 30-50% compared to hyperscaler GPU instances.

This skill pack provides real kubectl commands, YAML manifests, and Python patterns for every stage of CoreWeave deployment.

## Installation

```bash
/plugin install coreweave-pack@claude-code-plugins-plus
```

## Skills Included

### Getting Started (S01-S04)

| Skill | Description |
|-------|-------------|
| `coreweave-install-auth` | Kubeconfig setup, API token, GPU access verification |
| `coreweave-hello-world` | First GPU pod: vLLM inference server and batch CUDA job |
| `coreweave-local-dev-loop` | Container build, YAML validation, deploy-watch cycle |
| `coreweave-sdk-patterns` | GPU affinity helpers, inference client, deployment generators |

### Core Workflows (S05-S08)

| Skill | Description |
|-------|-------------|
| `coreweave-core-workflow-a` | KServe InferenceService with autoscaling and scale-to-zero |
| `coreweave-core-workflow-b` | Distributed GPU training with PyTorch DDP and shared storage |
| `coreweave-common-errors` | Pod Pending, CUDA OOM, NCCL timeout, image pull failures |
| `coreweave-debug-bundle` | Collect node status, GPU allocation, and pod logs for support |

### Operations (S09-S12)

| Skill | Description |
|-------|-------------|
| `coreweave-rate-limits` | GPU quota management and inference request queuing |
| `coreweave-security-basics` | Secrets for model tokens, network policies, RBAC |
| `coreweave-prod-checklist` | Production readiness for inference and training workloads |
| `coreweave-upgrade-migration` | GPU type migration (A100 to H100), CUDA version upgrades |

### Pro Skills (P13-P18)

| Skill | Description |
|-------|-------------|
| `coreweave-ci-integration` | GitHub Actions for container build and CKS deployment |
| `coreweave-deploy-integration` | Helm charts and Kustomize overlays for GPU deployments |
| `coreweave-webhooks-events` | Kubernetes event monitoring, GPU metrics, Slack alerts |
| `coreweave-performance-tuning` | GPU selection, vLLM batching, HPA with DCGM metrics |
| `coreweave-cost-tuning` | GPU pricing comparison, scale-to-zero, quantization savings |
| `coreweave-reference-architecture` | Multi-model inference platform architecture |

### Flagship Skills (F19-F24)

| Skill | Description |
|-------|-------------|
| `coreweave-multi-env-setup` | Dev/staging/prod with different GPU types and quotas |
| `coreweave-observability` | DCGM GPU metrics, Prometheus alerts, Grafana dashboards |
| `coreweave-incident-runbook` | GPU workload failure triage and remediation |
| `coreweave-data-handling` | PVC storage classes, model downloading, dataset management |
| `coreweave-enterprise-rbac` | Namespace isolation, GPU quotas per team, role bindings |
| `coreweave-migration-deep-dive` | Migrate from AWS/GCP GPU instances to CoreWeave CKS |

## Quick Start

### 1. Install the Pack

```bash
/plugin install coreweave-pack@claude-code-plugins-plus
```

### 2. Configure kubectl

Download your kubeconfig from [cloud.coreweave.com](https://cloud.coreweave.com) and set it up:

```bash
export KUBECONFIG=~/.kube/coreweave
kubectl get nodes
```

### 3. Deploy Your First GPU Workload

```bash
# Run nvidia-smi on an A100
kubectl run gpu-test --image=nvidia/cuda:12.2.0-base-ubuntu22.04 \
  --restart=Never \
  --overrides='{"spec":{"containers":[{"name":"gpu-test","image":"nvidia/cuda:12.2.0-base-ubuntu22.04","command":["nvidia-smi"],"resources":{"limits":{"nvidia.com/gpu":"1"}}}]}}' \
  -- nvidia-smi

kubectl logs gpu-test
kubectl delete pod gpu-test
```

### 4. Deploy an Inference Service

Follow `coreweave-core-workflow-a` to deploy a KServe InferenceService with autoscaling.

## Key CoreWeave Links

- [CoreWeave Documentation](https://docs.coreweave.com) -- CKS and platform docs
- [GPU Instance Types](https://docs.coreweave.com/docs/platform/instances/gpu-instances) -- available GPUs
- [CoreWeave Pricing](https://www.coreweave.com/pricing) -- per-GPU-hour pricing
- [CKS Introduction](https://docs.coreweave.com/docs/products/cks) -- Kubernetes service overview
- [CoreWeave Examples](https://github.com/coreweave/kubernetes-cloud) -- sample YAML manifests
- [CoreWeave Status](https://status.coreweave.com) -- platform status page

## License

MIT
