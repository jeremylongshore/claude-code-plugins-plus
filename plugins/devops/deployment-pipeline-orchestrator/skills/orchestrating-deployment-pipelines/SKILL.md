---
name: orchestrating-deployment-pipelines
description: |
  Deploy use when you need to work with deployment and CI/CD.
  This skill provides deployment automation and orchestration with comprehensive guidance and automation.
  Trigger with phrases like "deploy application", "create pipeline",
  or "automate deployment".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(git:*), Bash(docker:*), Bash(kubectl:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Orchestrating Deployment Pipelines

## Overview

Orchestrate multi-stage deployment pipelines that coordinate builds, tests, approvals, and releases across environments (dev, staging, production). Implement deployment strategies including blue-green, canary, rolling updates, and feature flags using Kubernetes, cloud-native services, and CI/CD platforms.

## Prerequisites

- CI/CD platform configured (GitHub Actions, GitLab CI, Jenkins, ArgoCD)
- Kubernetes cluster with `kubectl` access or cloud deployment target (ECS, Cloud Run, App Engine)
- Container registry with built and tagged images ready for deployment
- Environment-specific configuration (secrets, environment variables) stored securely
- Monitoring and alerting configured to detect deployment failures

## Instructions

1. Define the deployment topology: target environments, promotion flow (dev -> staging -> production), and approval gates
2. Select deployment strategy per environment: rolling update for staging, canary or blue-green for production
3. Generate deployment manifests (Kubernetes Deployments, Services, Ingress) or cloud service configurations
4. Implement pre-deployment checks: database migration status, dependency health, configuration validation
5. Configure canary analysis: route 5-10% of traffic to new version, monitor error rate and latency for 15 minutes before full rollout
6. Add post-deployment verification: smoke tests, health check endpoints, synthetic monitoring
7. Implement automated rollback triggers: revert if error rate exceeds 1% or P99 latency doubles during canary phase
8. Set up deployment notifications: Slack messages with deployment status, version, environment, and commit link
9. Document the deployment runbook with manual intervention procedures for edge cases

## Output

- Deployment pipeline configurations (GitHub Actions workflows, ArgoCD Applications)
- Kubernetes manifests with deployment strategy annotations
- Canary analysis configuration (Flagger, Argo Rollouts)
- Pre/post-deployment hook scripts
- Deployment runbook with rollback procedures

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `ImagePullBackOff` | Image tag not found in registry or auth failure | Verify image exists with `docker manifest inspect`; check `imagePullSecrets` |
| `CrashLoopBackOff` | Application failing to start in new version | Check pod logs with `kubectl logs`; verify environment variables and config maps |
| `Canary analysis failed` | Error rate or latency exceeded threshold during canary | Automatic rollback triggered; investigate logs from canary pods before retrying |
| `Deployment stuck in Progressing` | Insufficient resources or pod scheduling failure | Check `kubectl describe deployment` for events; verify resource requests and node capacity |
| `Database migration failed` | Schema conflict or lock timeout | Run migrations independently before deployment; add retry logic and connection timeout |

## Examples

- "Create a deployment pipeline that builds on PR merge, deploys to staging automatically, runs integration tests, then requires manual approval for production with canary rollout."
- "Set up Argo Rollouts for a Kubernetes deployment with 10% canary traffic, Prometheus-based analysis, and automatic rollback on error rate > 0.5%."
- "Generate a blue-green deployment for an ECS service with ALB target group switching and automatic rollback on health check failure."

## Resources

- Kubernetes deployment strategies: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
- Argo Rollouts: https://argoproj.github.io/argo-rollouts/
- Flagger (progressive delivery): https://flagger.app/
- AWS ECS blue-green: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-bluegreen.html