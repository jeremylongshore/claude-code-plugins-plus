---
name: coreweave-security-basics
description: |
  Secure CoreWeave deployments with RBAC, network policies, and secrets management.
  Use when hardening GPU workloads, managing model access,
  or configuring namespace isolation.
  Trigger with phrases like "coreweave security", "coreweave rbac",
  "secure coreweave", "coreweave secrets".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, gpu-cloud, kubernetes, inference, coreweave]
compatible-with: claude-code
---

# CoreWeave Security Basics

## Instructions

### Secrets for Model Access

```bash
# HuggingFace token
kubectl create secret generic hf-token --from-literal=token="${HF_TOKEN}"

# Container registry credentials
kubectl create secret docker-registry regcred \
  --docker-server=ghcr.io \
  --docker-username=$USER \
  --docker-password=$TOKEN
```

### Network Policy for Inference Pods

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: inference-isolation
spec:
  podSelector:
    matchLabels:
      app: inference-server
  policyTypes: [Ingress, Egress]
  ingress:
    - from:
        - podSelector:
            matchLabels:
              role: api-gateway
      ports:
        - port: 8080
  egress:
    - to: []  # Allow all egress for model downloads
      ports:
        - port: 443
```

### Security Checklist

- [ ] Kubeconfig stored securely, not in repos
- [ ] Secrets used for model tokens (not env vars in YAML)
- [ ] Network policies restrict inference endpoint access
- [ ] RBAC limits namespace access per team
- [ ] Container images scanned for CVEs
- [ ] PVCs encrypted at rest

## Resources

- [CoreWeave CKS Security](https://docs.coreweave.com/docs/products/cks)

## Next Steps

For production readiness, see `coreweave-prod-checklist`.
