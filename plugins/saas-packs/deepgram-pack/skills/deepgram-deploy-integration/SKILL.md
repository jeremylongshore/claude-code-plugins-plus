---
name: deepgram-deploy-integration
description: |
  Deploy Deepgram integrations to production environments.
  Use when deploying to cloud platforms, configuring production infrastructure,
  or setting up Deepgram in containerized environments.
  Trigger with phrases like "deploy deepgram", "deepgram docker",
  "deepgram kubernetes", "deepgram production deploy", "deepgram cloud".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Deepgram Deploy Integration

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Deploy Deepgram integrations to various cloud platforms and container environments including Docker, Kubernetes, AWS Lambda, Google Cloud Run, and Vercel.

## Prerequisites
- Production API key ready
- Infrastructure access configured
- Secret management in place
- Monitoring configured

## Instructions

### Step 1: Containerize with Docker
Build a multi-stage Dockerfile with non-root user, health checks, and production optimizations.

### Step 2: Configure Orchestration
Choose deployment target: Docker Compose (simple), Kubernetes (scale), or serverless (event-driven).

### Step 3: Manage Secrets
Use platform-native secret management (K8s Secrets, AWS Secrets Manager, GCP Secret Manager).

### Step 4: Set Up Health Checks
Configure liveness and readiness probes against `/health` endpoint.

### Step 5: Configure Auto-scaling
Set up HPA (Kubernetes) or managed scaling with CPU-based thresholds at 70% utilization.

### Step 6: Create Deploy Script
Build environment-aware deploy script that runs build, tests, deploys, and smoke tests.

## Output
- Dockerfile with multi-stage build and health checks
- Docker Compose or Kubernetes manifests
- Serverless configuration (Lambda/Cloud Run/Vercel)
- Deploy script with environment selection
- Auto-scaling configuration

## Error Handling
| Issue | Cause | Resolution |
|-------|-------|------------|
| Container fails to start | Missing secret or env var | Check secret mounts and env config |
| Health check failing | Service not ready | Increase `initialDelaySeconds` |
| OOM kills | Memory limit too low | Increase memory limit (512Mi minimum) |
| Connection refused | Wrong port mapping | Verify `containerPort` matches app |

## Examples

### Quick Docker Build & Run
```bash
set -euo pipefail
docker build -t deepgram-service .
docker run -p 3000:3000 -e DEEPGRAM_API_KEY=$DEEPGRAM_API_KEY deepgram-service  # 3000: 3 seconds in ms
```

### Deploy Script Usage
```bash
./scripts/deploy.sh staging    # Deploy to staging
./scripts/deploy.sh production # Deploy to production
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [AWS Lambda with Node.js](https://docs.aws.amazon.com/lambda/latest/dg/lambda-nodejs.html)
- [Google Cloud Run](https://cloud.google.com/run/docs)