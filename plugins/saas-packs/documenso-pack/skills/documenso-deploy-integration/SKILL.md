---
name: documenso-deploy-integration
description: |
  Deploy Documenso integrations across different platforms and environments.
  Use when deploying to cloud platforms, containerizing applications,
  or setting up infrastructure for Documenso integrations.
  Trigger with phrases like "deploy documenso", "documenso docker",
  "documenso kubernetes", "documenso cloud deployment".
allowed-tools: Read, Write, Edit, Bash(docker:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Documenso Deploy Integration

## Overview
Deploy Documenso integrations to various platforms including Docker, Kubernetes, and serverless environments.

## Prerequisites
- Application ready for deployment
- Cloud platform account (AWS, GCP, Azure)
- Container runtime (Docker)
- Kubernetes cluster (for K8s deployment)

## Instructions

### Step 1: Docker Deployment
FROM node:20-alpine AS base
### Step 2: Kubernetes Deployment
apiVersion: apps/v1
### Step 3: AWS Lambda Deployment
// handler.ts
### Step 4: Google Cloud Run
steps:
### Step 5: Environment Configuration
// src/config.ts

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Docker Deployment
- Kubernetes Deployment
- AWS Lambda Deployment
- Google Cloud Run
- Environment Configuration

## Error Handling
| Deployment Issue | Cause | Solution |
|-----------------|-------|----------|
| Container crash | Missing env vars | Check secret mounting |
| Health check fail | App not ready | Increase startup time |
| Network timeout | Firewall rules | Allow egress to Documenso |
| OOM killed | Memory limit | Increase resources |

## Resources
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [AWS Lambda](https://docs.aws.amazon.com/lambda/)
- [Google Cloud Run](https://cloud.google.com/run/docs)

## Next Steps
For webhook configuration, see `documenso-webhooks-events`.

## Examples

**Basic usage**: Apply documenso deploy integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize documenso deploy integration for production environments with multiple constraints and team-specific requirements.