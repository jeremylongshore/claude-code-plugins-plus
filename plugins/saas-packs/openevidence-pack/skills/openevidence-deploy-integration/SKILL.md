---
name: openevidence-deploy-integration
description: |
  Deploy OpenEvidence integrations to healthcare production environments.
  Use when deploying to production, setting up staging environments,
  or configuring cloud deployments for clinical AI applications.
  Trigger with phrases like "deploy openevidence", "openevidence staging",
  "openevidence production deploy", "release openevidence".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# OpenEvidence Deploy Integration

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Deploy OpenEvidence clinical AI integrations to production healthcare environments with canary releases, Kubernetes manifests, health checks, and rollback procedures.

## Prerequisites
- CI pipeline configured (see `openevidence-ci-integration`)
- Production credentials from OpenEvidence
- Cloud platform configured (GCP, AWS, Azure)
- Signed BAA for production environment

## Instructions

### Step 1: Multi-Environment Configuration
Define environment configs (dev/staging/prod) with baseUrl, timeout, retries, secret paths, and feature flags.

### Step 2: Create Deployment Workflow
Build GitHub Actions workflow with test -> build -> deploy-staging -> deploy-production stages. Use canary releases for production (no-traffic deploy, 10% canary, monitor, full rollout).

### Step 3: Configure Kubernetes
Create Deployment (3 replicas), Service, Ingress, and HPA manifests. Use K8s secrets for API credentials, liveness/readiness probes against `/health`.

### Step 4: Implement Health Checks
Create `/health` (basic) and `/health/openevidence` (deep) endpoints that verify API connectivity and report latency.

### Step 5: Prepare Rollback
Create rollback script that lists recent revisions, identifies previous, and shifts traffic back with health verification.

## Output
- Multi-environment deployment configuration
- CI/CD pipeline with canary releases
- Kubernetes deployment manifests (Deployment, Service, Ingress, HPA)
- Health check endpoints (basic + deep)
- Rollback procedures and scripts

## Error Handling
| Deployment Issue | Detection | Resolution |
|------------------|-----------|------------|
| Health check fails | Readiness probe | Rollback to previous revision |
| High error rate | Monitoring alert | Rollback, investigate logs |
| Secret missing | Container fails to start | Check secret manager |
| Rate limit hit | 429 errors spike | Scale down, check quotas |

## Examples

### Deploy to Staging
```bash
gcloud run deploy clinical-evidence-api-staging \
  --image $IMAGE --region us-central1 \
  --set-env-vars NODE_ENV=staging \
  --set-secrets OPENEVIDENCE_API_KEY=openevidence-staging-api-key:latest
```

### Rollback Production
```bash
gcloud run services update-traffic clinical-evidence-api \
  --region us-central1 --to-revisions PREVIOUS_REVISION=100
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
