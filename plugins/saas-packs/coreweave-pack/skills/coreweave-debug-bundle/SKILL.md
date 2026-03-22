---
name: coreweave-debug-bundle
description: |
  Collect CoreWeave cluster diagnostics for support tickets.
  Use when preparing a support case, collecting GPU node status,
  or documenting pod failures.
  Trigger with phrases like "coreweave debug", "coreweave support",
  "coreweave diagnostics", "collect coreweave logs".
allowed-tools: Read, Bash(kubectl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, gpu-cloud, kubernetes, inference, coreweave]
compatible-with: claude-code
---

# CoreWeave Debug Bundle

## Instructions

```bash
#!/bin/bash
set -euo pipefail
BUNDLE="coreweave-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

kubectl get nodes -o wide > "$BUNDLE/nodes.txt"
kubectl get pods --all-namespaces -o wide > "$BUNDLE/pods.txt"
kubectl get events --sort-by=.lastTimestamp > "$BUNDLE/events.txt"
kubectl describe nodes | grep -A10 "Allocated resources" > "$BUNDLE/gpu-allocation.txt"

# Pod logs for failing pods
for pod in $(kubectl get pods --field-selector=status.phase=Failed -o name); do
  kubectl logs "$pod" --tail=100 > "$BUNDLE/$(basename $pod)-logs.txt" 2>&1
done

tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Resources

- [CoreWeave Support](https://www.coreweave.com/support)

## Next Steps

For rate limit handling, see `coreweave-rate-limits`.
