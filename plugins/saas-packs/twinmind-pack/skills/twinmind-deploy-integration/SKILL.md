---
name: twinmind-deploy-integration
description: |
  Deploy TwinMind integrations to production environments.
  Use when deploying to cloud platforms, configuring production infrastructure,
  or setting up deployment automation.
  Trigger with phrases like "deploy twinmind", "twinmind production deploy",
  "twinmind cloud deployment", "twinmind infrastructure".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(docker:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# TwinMind Deploy Integration

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Deploy TwinMind integrations to production cloud environments with Docker, AWS ECS/Fargate, GCP Cloud Run, Kubernetes, and GitHub Actions deployment pipelines.

## Prerequisites
- Completed `twinmind-ci-integration` setup
- Cloud provider account (AWS, GCP, or Azure)
- Docker installed
- Terraform or Pulumi for IaC

## Instructions

### Step 1: Docker Configuration
Create multi-stage Dockerfile (builder + runner) with non-root user, health check, and production NODE_ENV. Add docker-compose.yml with service replicas, resource limits, Redis, and logging config.

### Step 2: AWS Deployment (ECS/Fargate)
Write Terraform for Secrets Manager (API key + webhook secret), ECS cluster with container insights, Fargate task definition with secrets injection, ECS service with deployment circuit breaker, and CPU-based auto-scaling (2-10 instances, target 70%).

### Step 3: GCP Deployment (Cloud Run)
Write Terraform for Secret Manager, Cloud Run v2 service with auto-scaling (1-10 instances), startup/liveness probes, service account with secret accessor role.

### Step 4: Kubernetes Deployment
Create Deployment (2 replicas, resource limits, readiness/liveness probes, non-root security context), Service (ClusterIP), and HorizontalPodAutoscaler (CPU target 70%, 2-10 replicas).

### Step 5: GitHub Actions Deployment
Create deploy workflow: build-and-push to ECR, deploy-staging (wait for stable), deploy-production (manual approval via environment protection).

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete Dockerfile, Terraform modules, Kubernetes manifests, and deployment workflow.

## Output
- Docker configuration files
- AWS ECS/Fargate Terraform
- GCP Cloud Run Terraform
- Kubernetes manifests
- GitHub Actions deployment workflow

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Image pull failed | Registry auth | Verify credentials |
| Health check failed | Service not ready | Increase start period |
| Scaling not working | Metrics missing | Check monitoring config |
| Secrets not found | IAM permissions | Update service account |

## Examples
```dockerfile
# Multi-stage build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
RUN adduser -S twinmind -u 1001
COPY --from=builder /app/dist ./dist
USER twinmind
CMD ["node", "dist/index.js"]
```

```bash
# Deploy to ECS
aws ecs update-service --cluster twinmind-production \
  --service twinmind-service --force-new-deployment
aws ecs wait services-stable --cluster twinmind-production \
  --services twinmind-service
```

## Resources
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [GCP Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

## Next Steps
For webhook handling, see `twinmind-webhooks-events`.
