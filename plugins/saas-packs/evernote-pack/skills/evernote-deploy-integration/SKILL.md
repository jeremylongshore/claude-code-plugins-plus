---
name: evernote-deploy-integration
description: |
  Deploy Evernote integrations to production environments.
  Use when deploying to cloud platforms, configuring production,
  or setting up deployment pipelines.
  Trigger with phrases like "deploy evernote", "evernote production deploy",
  "release evernote", "evernote cloud deployment".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Deploy Integration

## Overview
Deploy Evernote integrations to production environments including cloud platforms, containerized deployments, and serverless architectures.

## Prerequisites
- CI/CD pipeline configured
- Production API credentials approved
- Cloud platform account (AWS, GCP, Azure)
- Docker installed (for containerized deployments)

## Instructions

### Step 1: Docker Deployment

### Step 2: AWS Deployment (ECS/Fargate)

### Step 3: GitHub Actions Deployment

### Step 4: Google Cloud Run Deployment

### Step 5: Serverless Deployment (AWS Lambda)

### Step 6: Kubernetes Deployment

### Step 7: Deployment Verification

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Docker containerization setup
- AWS ECS/Fargate deployment
- GitHub Actions CI/CD pipeline
- Google Cloud Run deployment
- Serverless (Lambda) deployment
- Kubernetes deployment

## Resources
- [AWS ECS Documentation](https://docs.aws.amazon.com/ecs/)
- [Google Cloud Run](https://cloud.google.com/run/docs)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Serverless Framework](https://www.serverless.com/framework/docs)

## Next Steps
For webhook handling, see `evernote-webhooks-events`.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with CI/CD |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply evernote deploy integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize evernote deploy integration for production environments with multiple constraints and team-specific requirements.