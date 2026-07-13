# oraclecloud-deploy-integration — One-Pager

Deploy containerized applications to OCI using OKE (Kubernetes) or Container Instances with working manifests.

## The Problem

OKE (Kubernetes) setup requires VCN, node pool, OCIR registry, and IAM policies — 4x more config than EKS. Container Instances are simpler but underdocumented. Teams either over-invest in Kubernetes for simple workloads or struggle through the multi-step OKE setup without a clear guide covering all the dependencies (VCN, subnets, node pools, registry auth, pull secrets).

## The Solution

This skill covers both deployment paths with working code. For OKE, it walks through OCIR image push, cluster creation via Python SDK, node pool configuration, kubeconfig setup, and a full deployment manifest with load balancer. For Container Instances, it provides the simpler serverless path for workloads that don't need Kubernetes orchestration.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | DevOps engineers and developers deploying containerized applications to OCI |
| **What** | Complete container deployment workflow: OCIR push, OKE cluster/node pool, kubectl config, deployment manifests, and Container Instances alternative |
| **When** | Deploying a new service to OCI, migrating from another cloud's container platform, or evaluating OKE vs Container Instances |

## Key Features

1. **Dual deployment paths** — Full OKE Kubernetes setup and simpler Container Instances for different workload needs
2. **OCIR registry auth** — Docker login, image push, and Kubernetes pull secret configuration
3. **SDK-driven provisioning** — Cluster and node pool creation via `oci.container_engine.ContainerEngineClient`

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
