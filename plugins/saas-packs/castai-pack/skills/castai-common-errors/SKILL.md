---
name: castai-common-errors
description: |
  Diagnose and fix CAST AI agent, API, and autoscaler errors.
  Use when the CAST AI agent is offline, nodes are not scaling,
  or API calls return errors.
  Trigger with phrases like "cast ai error", "cast ai not working",
  "cast ai agent offline", "cast ai debug", "fix cast ai".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, kubernetes, cost-optimization, castai]
compatible-with: claude-code
---

# CAST AI Common Errors

## Overview

Diagnostic guide for the 10 most common CAST AI issues, covering agent connectivity, API errors, autoscaler failures, and node provisioning problems.

## Prerequisites

- `kubectl` access to the cluster
- `CASTAI_API_KEY` configured
- Access to CAST AI console for log correlation

## Error Reference

### 1. Agent Pod CrashLoopBackOff

```bash
kubectl get pods -n castai-agent
kubectl logs -n castai-agent deployment/castai-agent --tail=50
```

**Causes and fixes:**
- **Invalid API key**: Regenerate at console.cast.ai > API
- **Wrong provider**: Set `--set provider=eks|gke|aks` correctly in Helm
- **RBAC missing**: Apply the required ClusterRole and ClusterRoleBinding
- **Network blocked**: Ensure outbound HTTPS to `api.cast.ai` is allowed

### 2. Agent Shows "Disconnected" in Console

```bash
# Check agent heartbeat
kubectl logs -n castai-agent deployment/castai-agent | grep -i "heartbeat\|connect\|error"

# Verify network connectivity from inside the cluster
kubectl run castai-debug --image=curlimages/curl --rm -it --restart=Never -- \
  curl -s -o /dev/null -w "%{http_code}" https://api.cast.ai/v1/kubernetes/external-clusters
```

**Fix**: Restart the agent pod: `kubectl rollout restart deployment/castai-agent -n castai-agent`

### 3. API Returns 401 Unauthorized

```bash
# Test API key
curl -s -o /dev/null -w "%{http_code}" \
  -H "X-API-Key: ${CASTAI_API_KEY}" \
  https://api.cast.ai/v1/kubernetes/external-clusters
# Should return 200, not 401
```

**Fix**: Generate a new API key at console.cast.ai > API > API Access Keys.

### 4. Nodes Not Scaling Up (Unschedulable Pods)

```bash
# Check for pending pods
kubectl get pods --all-namespaces --field-selector=status.phase=Pending

# Verify unschedulable pods policy is enabled
curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
  "https://api.cast.ai/v1/kubernetes/clusters/${CASTAI_CLUSTER_ID}/policies" \
  | jq '.unschedulablePods'
```

**Causes:**
- `unschedulablePods.enabled` is `false` -- enable it
- Cluster limits reached -- increase `clusterLimits.cpu.maxCores`
- No matching node template -- check constraints match pod requirements

### 5. Nodes Not Scaling Down (Empty Nodes)

```bash
# Check node downscaler configuration
curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
  "https://api.cast.ai/v1/kubernetes/clusters/${CASTAI_CLUSTER_ID}/policies" \
  | jq '.nodeDownscaler'
```

**Causes:**
- `nodeDownscaler.enabled` is `false`
- Pods with `PodDisruptionBudget` blocking eviction
- DaemonSet-only nodes with system pods preventing drain
- Delay too high -- reduce `emptyNodes.delaySeconds`

### 6. Spot Instance Fallback Not Working

```bash
# Check spot configuration
curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
  "https://api.cast.ai/v1/kubernetes/clusters/${CASTAI_CLUSTER_ID}/policies" \
  | jq '.spotInstances'
```

**Fix**: Enable `spotDiversityEnabled: true` and set `spotDiversityPriceIncreaseLimitPercent` to 20-30 for better availability.

### 7. Evictor Too Aggressive

Symptoms: Pods being evicted too frequently, service disruption.

```bash
kubectl get events --field-selector reason=Evicted -A --sort-by=.lastTimestamp | tail -20
```

**Fix**: Increase evictor cycle interval or switch to non-aggressive mode:
```bash
helm upgrade castai-evictor castai-helm/castai-evictor \
  -n castai-agent \
  --set castai.apiKey="${CASTAI_API_KEY}" \
  --set castai.clusterID="${CASTAI_CLUSTER_ID}" \
  --set evictor.aggressiveMode=false \
  --set evictor.cycleInterval=600
```

### 8. Terraform State Drift

```bash
terraform plan -var-file=environments/prod.tfvars
# If drift detected:
terraform refresh -var-file=environments/prod.tfvars
```

**Fix**: Avoid mixing Terraform and console-based policy changes. Pick one source of truth.

### 9. Helm Chart Version Mismatch

```bash
# Check installed versions
helm list -n castai-agent
helm search repo castai-helm --versions | head -10

# Update to latest
helm repo update
helm upgrade castai-agent castai-helm/castai-agent -n castai-agent \
  --reuse-values
```

### 10. Workload Autoscaler Not Recommending

```bash
kubectl logs -n castai-agent deployment/castai-workload-autoscaler --tail=50
```

**Causes:**
- Insufficient metrics data (wait 24h)
- Missing annotation `autoscaling.cast.ai/enabled: "true"`
- Workload autoscaler pod not running

## Escalation Path

1. Collect debug info: Helm releases, agent logs, cluster events
2. Check https://status.cast.ai for platform issues
3. Contact support with cluster ID and screenshots

## Resources

- [CAST AI Troubleshooting](https://docs.cast.ai/docs/casti-ai-components)
- [CAST AI Status](https://status.cast.ai)
- [Autoscaler Checklist](https://docs.cast.ai/docs/autoscaler-checklist)

## Next Steps

For comprehensive diagnostics, see `castai-debug-bundle`.
