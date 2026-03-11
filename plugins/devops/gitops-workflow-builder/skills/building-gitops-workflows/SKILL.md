---
name: building-gitops-workflows
description: |
  Execute use when constructing GitOps workflows using ArgoCD or Flux. Trigger with phrases like "create GitOps workflow", "setup ArgoCD", "configure Flux", or "automate Kubernetes deployments". Generates production-ready configurations, implements best practices, and ensures security-first approach for continuous deployment.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(kubectl:*), Bash(git:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Building GitOps Workflows

## Overview

Construct GitOps workflows using ArgoCD or Flux to implement declarative, Git-driven continuous delivery for Kubernetes. Generate Application/Kustomization manifests, configure sync policies, set up multi-environment promotion, and implement RBAC and notification integrations.

## Prerequisites

- Kubernetes cluster accessible via `kubectl` with admin permissions
- Git repository for storing Kubernetes manifests (separate from application code recommended)
- ArgoCD or Flux installed on the cluster, or Helm charts ready for installation
- Container images built and pushed to a registry accessible from the cluster
- SSH key or access token for Git repository authentication from the cluster

## Instructions

1. Choose the GitOps tool based on requirements: ArgoCD for UI-driven management, Flux for lightweight Git-native approach
2. Design the repository structure: `environments/{dev,staging,prod}/` with Kustomize overlays or Helm values per environment
3. Generate ArgoCD Application or Flux Kustomization manifests pointing to the Git repository path for each environment
4. Configure sync policy: enable `automated.selfHeal` and `automated.prune` for non-production; use manual sync for production
5. Set up Git repository credentials as a Kubernetes Secret for the GitOps operator
6. Implement environment promotion: update the image tag in staging manifests, test, then promote to production via PR
7. Configure notifications: Slack/email alerts on sync success, failure, or health degradation via ArgoCD Notifications or Flux Alert Provider
8. Add RBAC: restrict who can sync production applications and who can modify GitOps configurations
9. Validate the setup: push a manifest change to Git and verify the GitOps operator detects and applies it within the sync interval

## Output

- ArgoCD Application or Flux Kustomization manifests per environment
- Git repository structure with Kustomize bases and overlays
- RBAC configuration (ArgoCD AppProject, Kubernetes RBAC)
- Notification configuration (Slack webhooks, email)
- CI pipeline step to update image tags in the GitOps repository after build

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `ComparisonError: Failed to load target state` | Invalid manifest path or Git ref | Verify `path:` and `targetRevision:` in the Application manifest; check repo structure |
| `Authentication failed for repository` | SSH key or token not configured or expired | Create/update the Git credentials Secret; verify deploy key has read access |
| `Application is OutOfSync but not syncing` | Automated sync disabled or sync window closed | Enable `automated:` in syncPolicy or trigger manual sync with `argocd app sync` |
| `Resource already exists and is not managed` | Resource created outside of GitOps | Add the `argocd.argoproj.io/managed-by` annotation or delete the conflicting resource |
| `Sync failed: health check timeout` | Application pods not becoming ready after sync | Check pod logs; verify resource requests fit node capacity; increase health check timeout |

## Examples

- "Set up ArgoCD with three Application manifests for dev, staging, and production, each pointing to a different Kustomize overlay in the GitOps repo."
- "Configure Flux with automatic image updates: scan ECR for new tags matching `v*`, update the staging manifests, and create a PR for production promotion."
- "Create an ArgoCD AppProject that restricts the production application to specific namespaces and requires manual sync with admin-only access."

## Resources

- ArgoCD documentation: https://argo-cd.readthedocs.io/en/stable/
- Flux documentation: https://fluxcd.io/flux/
- GitOps principles: https://opengitops.dev/
- Kustomize: https://kustomize.io/