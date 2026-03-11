---
name: managing-network-policies
description: |
  Execute use when managing Kubernetes network policies and firewall rules. Trigger with phrases like "create network policy", "configure firewall rules", "restrict pod communication", or "setup ingress/egress rules". Generates Kubernetes NetworkPolicy manifests following least privilege and zero-trust principles.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(kubectl:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Managing Network Policies

## Overview

Create and manage Kubernetes NetworkPolicy manifests to enforce zero-trust networking between pods, namespaces, and external endpoints. Generate ingress and egress rules with label selectors, namespace selectors, CIDR blocks, and port specifications following the principle of least privilege.

## Prerequisites

- Kubernetes cluster with a CNI plugin that supports NetworkPolicy (Calico, Cilium, Weave Net)
- `kubectl` configured with permissions to create and manage NetworkPolicy resources
- Pod labels consistently defined across deployments for accurate selector targeting
- Service communication map documenting which pods need to talk to which pods on which ports
- Understanding of DNS requirements (pods need egress to kube-dns on port 53 for name resolution)

## Instructions

1. Map the application communication patterns: identify all service-to-service, service-to-database, and service-to-external connections
2. Start with a default-deny policy for both ingress and egress in each namespace to establish zero-trust baseline
3. Add explicit allow rules for each legitimate communication path: specify source pod labels, destination pod labels, and ports
4. Always include a DNS egress rule allowing traffic to `kube-system` namespace on UDP/TCP port 53 for CoreDNS
5. Define egress rules for external API access: use CIDR blocks or namespaceSelector for known external services
6. Apply policies to a test namespace first and verify connectivity with `kubectl exec` curl/wget commands
7. Monitor for blocked traffic in the CNI plugin logs (Calico: `calicoctl node status`, Cilium: `cilium monitor`)
8. Iterate on policies: add missing allow rules for any legitimate traffic that gets blocked
9. Document each policy with annotations explaining the business reason for the allowed communication

## Output

- Default-deny NetworkPolicy manifests for ingress and egress per namespace
- Allow-list NetworkPolicy manifests for each service communication path
- DNS egress policy allowing pod name resolution
- External access egress policies with CIDR blocks
- Connectivity test commands for validation

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `All traffic blocked after applying policy` | Default-deny applied without corresponding allow rules | Apply allow rules before or simultaneously with deny policies; verify with `kubectl exec` tests |
| `DNS resolution fails after network policy` | Missing egress rule for kube-dns/CoreDNS | Add egress policy allowing UDP and TCP port 53 to `kube-system` namespace |
| `Policy not targeting intended pods` | Label mismatch between policy selector and pod labels | Verify labels with `kubectl get pods --show-labels`; match selectors exactly |
| `Traffic still allowed despite deny policy` | CNI plugin does not support NetworkPolicy or policy in wrong namespace | Verify CNI support with `kubectl get networkpolicy -A`; ensure policy is in the correct namespace |
| `Intermittent connection failures` | Policy allows traffic but connection pool or timeout settings too aggressive | Check if the issue is network policy or application-level; test with `kubectl exec` during failures |

## Examples

- "Create a default-deny policy for the `production` namespace, then add allow rules so only the ingress controller can reach web pods on port 443."
- "Generate egress policies that restrict the API pods to communicate only with PostgreSQL (port 5432), Redis (port 6379), and external HTTPS APIs."
- "Build a complete set of network policies for a 3-tier app: frontend -> API (8080), API -> database (5432), API -> cache (6379), all pods -> DNS (53)."

## Resources

- Kubernetes NetworkPolicy: https://kubernetes.io/docs/concepts/services-networking/network-policies/
- Calico network policy: https://docs.tigera.io/calico/latest/network-policy/
- Cilium network policy: https://docs.cilium.io/en/stable/security/policy/
- Network policy editor (visual): https://editor.networkpolicy.io/
