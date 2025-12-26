---
name: building-gitops-workflows
description: |
  Use when constructing GitOps workflows using ArgoCD or Flux. Trigger with phrases like "create GitOps workflow", "setup ArgoCD", "configure Flux", or "automate Kubernetes deployments". Generates production-ready configurations, implements best practices, and ensures security-first approach for continuous deployment.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(kubectl:*), Bash(git:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
## Prerequisites

Before using this skill, ensure:
- Kubernetes cluster is accessible and kubectl is configured
- Git repository is available for GitOps source
- ArgoCD or Flux is installed on the cluster (or ready to install)
- Appropriate RBAC permissions for GitOps operator
- Network connectivity between cluster and Git repository

## Instructions

1. **Select GitOps Tool**: Determine whether to use ArgoCD or Flux based on requirements
2. **Define Application Structure**: Establish repository layout with environment separation (dev/staging/prod)
3. **Generate Manifests**: Create Application/Kustomization files pointing to Git sources
4. **Configure Sync Policy**: Set automated or manual sync with self-heal and prune options
5. **Implement RBAC**: Define service accounts and role bindings for GitOps operator
6. **Set Up Monitoring**: Configure notifications and health checks for deployments
7. **Validate Configuration**: Test sync behavior and verify reconciliation loops

## Output

Generates GitOps workflow configurations including:

**ArgoCD Application Manifest:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: app-name
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/org/repo
    path: manifests/prod
    targetRevision: main
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

**Flux Kustomization:**
```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: app-name
  namespace: flux-system
spec:
  interval: 5m
  path: ./manifests/prod
  prune: true
  sourceRef:
    kind: GitRepository
    name: app-repo
```

## Error Handling

Common issues and solutions:

**Sync Failures**
- Error: "ComparisonError: Failed to load target state"
- Solution: Verify Git repository URL, credentials, and target path exist

**RBAC Permissions**
- Error: "User cannot create resource in API group"
- Solution: Grant GitOps service account appropriate cluster roles

**Out of Sync State**
- Warning: "Application is OutOfSync"
- Solution: Enable automated sync or manually sync via UI/CLI

**Git Authentication**
- Error: "Authentication failed for repository"
- Solution: Configure SSH keys or access tokens in {baseDir}/.git/config

**Resource Conflicts**
- Error: "Resource already exists and is not managed by GitOps"
- Solution: Import existing resources or remove conflicting manual deployments

## Resources

- ArgoCD documentation: https://argo-cd.readthedocs.io/
- Flux documentation: https://fluxcd.io/docs/
- GitOps principles and patterns guide
- Kubernetes manifest best practices
- Repository structure templates in {baseDir}/gitops-examples/

## Overview

This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.