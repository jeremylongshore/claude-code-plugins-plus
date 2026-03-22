---
name: castai-debug-bundle
description: |
  Collect CAST AI diagnostic bundle for support tickets and troubleshooting.
  Use when preparing a support case, collecting agent logs,
  or building a diagnostic snapshot of cluster state.
  Trigger with phrases like "cast ai debug", "cast ai support bundle",
  "collect cast ai diagnostics", "cast ai logs".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Bash(tar:*), Bash(helm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, kubernetes, cost-optimization, castai]
compatible-with: claude-code
---

# CAST AI Debug Bundle

## Overview

Collect all CAST AI component logs, cluster state, and configuration into a single archive for troubleshooting or support tickets. The bundle captures agent status, Helm releases, autoscaler policies, node inventory, and recent events.

## Prerequisites

- `kubectl` access to the cluster running CAST AI
- `CASTAI_API_KEY` and `CASTAI_CLUSTER_ID` configured
- `helm` installed

## Instructions

### Step 1: Run the Debug Bundle Script

```bash
#!/bin/bash
# castai-debug-bundle.sh
set -euo pipefail

BUNDLE_DIR="castai-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== CAST AI Debug Bundle ===" | tee "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u)" | tee -a "$BUNDLE_DIR/summary.txt"
echo "Cluster ID: ${CASTAI_CLUSTER_ID:-unknown}" | tee -a "$BUNDLE_DIR/summary.txt"

# 1. Helm releases
echo "--- Helm Releases ---" >> "$BUNDLE_DIR/summary.txt"
helm list -n castai-agent -o yaml > "$BUNDLE_DIR/helm-releases.yaml" 2>&1

# 2. Pod status
echo "--- Pod Status ---" >> "$BUNDLE_DIR/summary.txt"
kubectl get pods -n castai-agent -o wide > "$BUNDLE_DIR/pod-status.txt" 2>&1

# 3. Agent logs (last 200 lines each)
for deploy in castai-agent cluster-controller castai-evictor castai-spot-handler castai-workload-autoscaler; do
  kubectl logs -n castai-agent "deployment/$deploy" --tail=200 \
    > "$BUNDLE_DIR/${deploy}-logs.txt" 2>&1 || echo "Not found: $deploy" >> "$BUNDLE_DIR/summary.txt"
done

# 4. Cluster events (CAST AI related)
kubectl get events -n castai-agent --sort-by='.lastTimestamp' \
  > "$BUNDLE_DIR/events.txt" 2>&1

# 5. Node inventory
kubectl get nodes -o wide > "$BUNDLE_DIR/nodes.txt" 2>&1

# 6. API cluster status (redact API key from output)
if [ -n "${CASTAI_API_KEY:-}" ] && [ -n "${CASTAI_CLUSTER_ID:-}" ]; then
  curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
    "https://api.cast.ai/v1/kubernetes/external-clusters/${CASTAI_CLUSTER_ID}" \
    | jq '{name, status, agentStatus, providerType, createdAt}' \
    > "$BUNDLE_DIR/cluster-status.json" 2>&1

  curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
    "https://api.cast.ai/v1/kubernetes/clusters/${CASTAI_CLUSTER_ID}/policies" \
    > "$BUNDLE_DIR/policies.json" 2>&1
fi

# 7. RBAC check
kubectl get clusterrole -l app.kubernetes.io/managed-by=castai \
  > "$BUNDLE_DIR/rbac.txt" 2>&1

# 8. Package bundle
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"
```

### Step 2: Review Before Sharing

**Safe to include:**
- Pod logs (no secrets in CAST AI agent logs)
- Helm release metadata
- Node names and instance types
- Autoscaler policies
- Cluster events

**Redact before sharing:**
- API keys (the script never writes them)
- Custom environment variables
- Internal hostnames if sensitive

### Step 3: Submit to CAST AI Support

1. Generate bundle: `bash castai-debug-bundle.sh`
2. Attach `castai-debug-*.tar.gz` to support ticket at support.cast.ai
3. Include your cluster ID and a description of the issue

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `kubectl` permission denied | Missing RBAC | Use cluster-admin kubeconfig |
| Empty log files | Pod not running | Note which components are down |
| API call fails | Key expired | Bundle still useful with kubectl data |
| tar fails | Disk full | Clean temp files first |

## Resources

- [CAST AI Support](https://support.cast.ai)
- [CAST AI Status](https://status.cast.ai)
- [Component Troubleshooting](https://docs.cast.ai/docs/casti-ai-components)

## Next Steps

For rate limit handling, see `castai-rate-limits`.
