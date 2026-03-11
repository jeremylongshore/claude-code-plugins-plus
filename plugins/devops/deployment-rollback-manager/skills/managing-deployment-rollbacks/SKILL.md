---
name: managing-deployment-rollbacks
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

# Managing Deployment Rollbacks

## Overview

Implement and execute deployment rollback procedures for Kubernetes, ECS, Lambda, and cloud VM deployments. Detect failed deployments via health checks and error rate monitoring, then automatically or manually revert to the last known good version with minimal downtime and data integrity preservation.

## Prerequisites

- `kubectl` configured with cluster access and permission to manage deployments
- Deployment history retained (Kubernetes `revisionHistoryLimit`, ECS task definition versions)
- Monitoring system tracking error rate, latency, and health check status (Prometheus, Datadog, CloudWatch)
- Previous deployment artifacts (container images, task definitions) still available in the registry
- Database migration strategy that supports backward compatibility (expand-contract pattern)

## Instructions

1. Detect deployment failure: monitor error rate, P99 latency, pod restart count, and health check responses for 5-10 minutes post-deploy
2. Assess rollback scope: determine if the issue is application code, configuration, or infrastructure
3. For Kubernetes: execute `kubectl rollout undo deployment/<name>` to revert to the previous revision
4. For ECS: update the service to use the previous task definition revision
5. For Lambda: point the alias back to the previous function version
6. Verify database compatibility: ensure the previous application version works with the current database schema (no forward-only migrations were applied)
7. Confirm rollback success: verify health checks pass, error rate returns to baseline, and user-facing functionality is restored
8. Generate a post-incident report: document what failed, when rollback was triggered, time to recovery, and root cause
9. Create automated rollback rules: configure Kubernetes readiness probes, Argo Rollouts analysis, or CloudWatch alarms to trigger rollback without manual intervention

## Output

- Rollback scripts for each deployment target (Kubernetes, ECS, Lambda)
- Automated rollback configuration (Kubernetes probes, Argo Rollouts AnalysisTemplate)
- Post-incident report template with timeline and root cause sections
- Monitoring dashboard with rollback trigger indicators
- Database migration rollback procedures (down migrations, backward-compatible schemas)

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `no rollout history found` | Revision history limit set to 0 or deployment was created fresh | Increase `revisionHistoryLimit` in deployment spec; manually specify the target image tag |
| `Rollback succeeded but errors persist` | Issue is in configuration or external dependency, not application code | Check ConfigMaps, Secrets, and external service health; rollback configuration changes separately |
| `Database schema incompatible after rollback` | Forward-only migration applied during failed deployment | Apply a down migration or use expand-contract pattern; never deploy breaking schema changes alongside code |
| `Old image no longer in registry` | Lifecycle policy deleted the previous image | Restore from backup or rebuild from the git tag; extend image retention for production tags |
| `Rollback causes service disruption` | Insufficient replicas during rollback transition | Set `maxUnavailable: 0` in rolling update strategy to ensure zero-downtime rollback |

## Examples

- "Roll back the production Kubernetes deployment to the previous revision after detecting a spike in 5xx errors."
- "Create an automated rollback policy using Argo Rollouts that reverts if error rate exceeds 1% during the first 10 minutes after deploy."
- "Generate a rollback runbook for an ECS service that includes steps to revert task definition, validate health, and notify the team via Slack."

## Resources

- Kubernetes rollout management: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment
- Argo Rollouts analysis: https://argoproj.github.io/argo-rollouts/features/analysis/
- AWS ECS rolling updates: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-ecs.html
- Database migration patterns: https://martinfowler.com/articles/evodb.html
