---
name: coreweave-enterprise-rbac
description: |
  Configure RBAC and namespace isolation for CoreWeave multi-team GPU access.
  Use when managing team permissions, isolating GPU quotas,
  or implementing namespace-level access control.
  Trigger with phrases like "coreweave rbac", "coreweave permissions",
  "coreweave namespace isolation", "coreweave team access".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, gpu-cloud, kubernetes, inference, coreweave]
compatible-with: claude-code
---

# CoreWeave Enterprise RBAC

## Namespace-Per-Team Pattern

```yaml
# Team namespace with GPU quota
apiVersion: v1
kind: ResourceQuota
metadata:
  name: ml-team-gpu-quota
  namespace: ml-team
spec:
  hard:
    requests.nvidia.com/gpu: "8"
    limits.nvidia.com/gpu: "8"
    persistentvolumeclaims: "10"
    requests.storage: 2Ti
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ml-team-access
  namespace: ml-team
subjects:
  - kind: Group
    name: ml-engineers
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: edit
  apiGroup: rbac.authorization.k8s.io
```

## Read-Only Access for Monitoring

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ml-team-readonly
  namespace: ml-team
subjects:
  - kind: Group
    name: ml-managers
roleRef:
  kind: ClusterRole
  name: view
  apiGroup: rbac.authorization.k8s.io
```

## Resources

- [CoreWeave CKS](https://docs.coreweave.com/docs/products/cks)
- [Kubernetes RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)

## Next Steps

For migration strategies, see `coreweave-migration-deep-dive`.
