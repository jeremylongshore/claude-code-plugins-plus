---
name: managing-network-policies
description: |
  Use when managing Kubernetes network policies and firewall rules. Trigger with phrases like "create network policy", "configure firewall rules", "restrict pod communication", or "setup ingress/egress rules". Generates Kubernetes NetworkPolicy manifests following least privilege and zero-trust principles.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(kubectl:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
## Prerequisites

Before using this skill, ensure:
- Kubernetes cluster has network policy support enabled
- Network plugin supports policies (Calico, Cilium, Weave)
- Pod labels are properly defined for policy selectors
- Understanding of application communication patterns
- Namespace isolation strategy is defined

## Instructions

1. **Identify Requirements**: Determine which pods need to communicate
2. **Define Selectors**: Use pod/namespace labels for policy targeting
3. **Configure Ingress**: Specify allowed incoming traffic sources and ports
4. **Configure Egress**: Define allowed outgoing traffic destinations
5. **Test Policies**: Verify connectivity works as expected
6. **Monitor Denials**: Check for blocked traffic in network plugin logs
7. **Iterate**: Refine policies based on application behavior

## Output

**Network Policy Examples:**
```yaml
# {baseDir}/network-policies/allow-frontend-to-backend.yaml


## Overview

This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
    - Ingress
  ingress:
    - from:
      - podSelector:
          matchLabels:
            app: frontend
      ports:
      - protocol: TCP
        port: 8080
---
# Deny all ingress by default
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Ingress
```

**Egress Policy:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-external-api
spec:
  podSelector:
    matchLabels:
      app: api-client
  policyTypes:
    - Egress
  egress:
    - to:
      - namespaceSelector:
          matchLabels:
            name: external-services
      ports:
      - protocol: TCP
        port: 443
```

## Error Handling

**Policy Not Applied**
- Error: Traffic still blocked/allowed contrary to policy
- Solution: Verify network plugin supports policies and policy is applied to correct namespace

**DNS Resolution Fails**
- Error: Pods cannot resolve DNS after applying policy
- Solution: Add egress rule allowing DNS traffic to kube-dns/coredns

**No Communication After Policy**
- Error: All traffic blocked unexpectedly
- Solution: Check for default-deny policies and ensure explicit allow rules exist

**Label Mismatch**
- Error: Policy not targeting intended pods
- Solution: Verify pod labels match policy selectors using `kubectl get pods --show-labels`

## Resources

- Kubernetes NetworkPolicy: https://kubernetes.io/docs/concepts/services-networking/network-policies/
- Calico documentation: https://docs.projectcalico.org/
- Example policies in {baseDir}/network-policy-examples/
