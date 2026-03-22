---
name: castai-security-basics
description: |
  Secure CAST AI API keys, RBAC configuration, and Kvisor security agent.
  Use when hardening CAST AI cluster access, configuring security scanning,
  or implementing API key rotation procedures.
  Trigger with phrases like "cast ai security", "cast ai api key rotation",
  "cast ai rbac", "cast ai kvisor", "secure cast ai".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(helm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, kubernetes, cost-optimization, castai]
compatible-with: claude-code
---

# CAST AI Security Basics

## Overview

Secure your CAST AI integration: API key management, RBAC least-privilege, Kvisor runtime security agent, and network policy configuration.

## Prerequisites

- CAST AI agent installed on cluster
- Cluster admin access for RBAC configuration
- Secrets manager (AWS Secrets Manager, Vault, etc.)

## Instructions

### Step 1: API Key Management

```bash
# Use separate keys per environment
# console.cast.ai > API > API Access Keys

# Development: Read-Only key (monitoring only)
# Staging: Full Access key with limited cluster scope
# Production: Full Access key, rotated every 90 days

# Store in secrets manager, never in code
aws secretsmanager create-secret \
  --name "castai/prod/api-key" \
  --secret-string "${CASTAI_API_KEY}"

# Rotate key procedure:
# 1. Generate new key in console
# 2. Update secrets manager
# 3. Restart CAST AI agent pods to pick up new key
# 4. Verify agent reconnects
# 5. Revoke old key in console
```

### Step 2: RBAC Least-Privilege Review

```bash
# Audit CAST AI ClusterRoles
kubectl get clusterroles -l app.kubernetes.io/managed-by=castai -o yaml

# The CAST AI agent needs these minimum permissions:
# - get/list/watch: pods, nodes, events, namespaces, replicasets
# - get: persistentvolumes, storageclasses
# The cluster controller additionally needs:
# - create/delete: nodes (for autoscaling)
# - patch: pods/eviction (for evictor)

# Check for overly broad permissions
kubectl auth can-i --list --as=system:serviceaccount:castai-agent:castai-agent
```

### Step 3: Enable Kvisor Security Agent

```bash
# Kvisor scans for CVEs, misconfigurations, and runtime threats
helm upgrade --install castai-kvisor castai-helm/castai-kvisor \
  -n castai-agent \
  --set castai.apiKey="${CASTAI_API_KEY}" \
  --set castai.clusterID="${CASTAI_CLUSTER_ID}" \
  --set controller.extraArgs.image-scan-enabled=true \
  --set controller.extraArgs.kube-bench-enabled=true

# Verify Kvisor is running
kubectl get pods -n castai-agent -l app.kubernetes.io/name=castai-kvisor
```

### Step 4: Network Policies

```yaml
# Restrict CAST AI agent egress to only api.cast.ai
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: castai-agent-egress
  namespace: castai-agent
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: castai-agent
  policyTypes:
    - Egress
  egress:
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0  # api.cast.ai resolves dynamically
      ports:
        - protocol: TCP
          port: 443
    - to:  # Allow DNS
        - namespaceSelector: {}
      ports:
        - protocol: UDP
          port: 53
```

### Step 5: Security Checklist

- [ ] API keys stored in secrets manager, not Helm values files
- [ ] Separate keys per environment (dev/staging/prod)
- [ ] Read-only keys for monitoring-only clusters
- [ ] Key rotation scheduled every 90 days
- [ ] Kvisor enabled for image scanning and CIS benchmarks
- [ ] CAST AI namespace has network policies
- [ ] Agent RBAC reviewed and minimized
- [ ] Helm values files in `.gitignore`
- [ ] Audit logs enabled in CAST AI console

## Error Handling

| Issue | Detection | Mitigation |
|-------|-----------|------------|
| API key in git history | `git log -S "CASTAI"` | Rotate key immediately |
| Agent has cluster-admin | `kubectl auth can-i --list` | Apply scoped ClusterRole |
| Kvisor high resource use | `kubectl top pods -n castai-agent` | Adjust scan intervals |
| Network policy blocks agent | Agent goes offline | Allow egress to 443 |

## Resources

- [CAST AI Security](https://docs.cast.ai/docs/kvisor)
- [Kvisor Agent](https://docs.cast.ai/docs/sec-runtime-security-installation)
- [CAST AI RBAC](https://docs.cast.ai/docs/cluster-controller)

## Next Steps

For production deployment checklist, see `castai-prod-checklist`.
