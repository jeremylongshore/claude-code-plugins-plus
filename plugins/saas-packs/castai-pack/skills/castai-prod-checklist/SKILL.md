---
name: castai-prod-checklist
description: |
  Production readiness checklist for CAST AI cluster onboarding.
  Use when going live with CAST AI autoscaling, validating Phase 2 setup,
  or preparing for production cost optimization.
  Trigger with phrases like "cast ai production", "cast ai go-live",
  "cast ai checklist", "cast ai launch".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Bash(helm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, kubernetes, cost-optimization, castai]
compatible-with: claude-code
---

# CAST AI Production Checklist

## Overview

Complete checklist for enabling CAST AI cost optimization on a production Kubernetes cluster. Covers Phase 1 (monitoring) through Phase 2 (full automation) with validation steps at each stage.

## Prerequisites

- CAST AI tested on a staging cluster first
- Production API key (Full Access)
- Change management approval for node lifecycle changes

## Phase 1: Monitoring Only

- [ ] Agent installed with read-only key
- [ ] Agent pod healthy: `kubectl get pods -n castai-agent`
- [ ] Console shows cluster as "Connected"
- [ ] Savings report generating (wait 24h for full data)
- [ ] Review savings estimate before enabling automation

## Phase 2: Autoscaling Enabled

- [ ] Full Access API key provisioned and stored in secrets manager
- [ ] Cluster controller installed
- [ ] Evictor installed with conservative settings (non-aggressive)
- [ ] Spot handler installed for graceful interruption handling
- [ ] Autoscaler policies configured with appropriate limits:
  - [ ] `clusterLimits.cpu.maxCores` set to safe ceiling
  - [ ] `unschedulablePods.headroom` configured (10-15%)
  - [ ] `nodeDownscaler.emptyNodes.delaySeconds` >= 300 for production
  - [ ] `spotInstances.spotDiversityEnabled` = true
- [ ] Node templates created for workload-specific needs (GPU, high-memory)
- [ ] PodDisruptionBudgets set on all critical workloads

## Workload Autoscaler

- [ ] Workload autoscaler installed
- [ ] Critical deployments annotated with min/max resource bounds
- [ ] Anti-shrink cooldown set (300s minimum)
- [ ] Memory headroom >= 20% for production workloads

## Security

- [ ] API key in secrets manager (not Helm values files)
- [ ] Kvisor security agent installed
- [ ] Network policies applied to castai-agent namespace
- [ ] RBAC reviewed and minimized
- [ ] Key rotation scheduled (90-day interval)

## Monitoring and Alerting

- [ ] Alert on agent pod restarts: `kube_pod_container_status_restarts_total{namespace="castai-agent"}`
- [ ] Alert on API errors in agent logs
- [ ] CAST AI console email notifications enabled
- [ ] Savings report reviewed weekly
- [ ] Dashboard tracking spot vs on-demand node ratio

## Rollback Procedure

```bash
# Disable autoscaling immediately (keeps agent monitoring)
curl -X PUT -H "X-API-Key: ${CASTAI_API_KEY}" \
  -H "Content-Type: application/json" \
  "https://api.cast.ai/v1/kubernetes/clusters/${CASTAI_CLUSTER_ID}/policies" \
  -d '{"enabled": false}'

# Or remove all CAST AI components
helm uninstall castai-evictor -n castai-agent
helm uninstall cluster-controller -n castai-agent
# Keep the agent for monitoring if desired
```

## Validation Commands

```bash
# Final pre-go-live verification
echo "=== CAST AI Production Validation ==="

# Agent healthy
kubectl get pods -n castai-agent -o wide

# All components running
helm list -n castai-agent

# Policies correct
curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
  "https://api.cast.ai/v1/kubernetes/clusters/${CASTAI_CLUSTER_ID}/policies" \
  | jq '{enabled, unschedulablePods: .unschedulablePods.enabled, downscaler: .nodeDownscaler.enabled, spot: .spotInstances.enabled}'

# Savings estimate
curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
  "https://api.cast.ai/v1/kubernetes/clusters/${CASTAI_CLUSTER_ID}/savings" \
  | jq '{monthly: .monthlySavings, percent: .savingsPercentage}'
```

## Resources

- [CAST AI Autoscaler Checklist](https://docs.cast.ai/docs/autoscaler-checklist)
- [CAST AI Status](https://status.cast.ai)

## Next Steps

For version upgrades, see `castai-upgrade-migration`.
