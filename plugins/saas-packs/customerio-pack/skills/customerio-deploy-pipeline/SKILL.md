---
name: customerio-deploy-pipeline
description: |
  Deploy Customer.io integrations to production.
  Use when deploying to cloud platforms, setting up
  production infrastructure, or automating deployments.
  Trigger with phrases like "deploy customer.io", "customer.io production",
  "customer.io cloud run", "customer.io kubernetes".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Customer.io Deploy Pipeline

## Overview
Deploy Customer.io integrations to production cloud platforms (GCP Cloud Run, Vercel, AWS Lambda, Kubernetes) with health checks and blue-green deployments.

## Prerequisites
- CI/CD pipeline configured
- Cloud platform access (GCP, AWS, Vercel, etc.)
- Production credentials ready

## Instructions

### Step 1: Deploy to Google Cloud Run
Set up GitHub Actions workflow with Workload Identity Federation, Docker build/push, and Cloud Run deployment with secrets from Secret Manager.

### Step 2: Deploy to Vercel (if applicable)
Configure Vercel project with serverless API functions for identify, track, and webhook endpoints.

### Step 3: Deploy to AWS Lambda (if applicable)
Use Serverless Framework with SSM parameter store for credentials and Lambda handlers for each API operation.

### Step 4: Deploy to Kubernetes
Create Deployment with secrets from SecretKeyRef, resource limits, readiness/liveness probes, and Service.

### Step 5: Implement Health Check
Build a health endpoint that tests Customer.io connectivity, reports status and latency, and includes version and uptime info.

### Step 6: Set Up Blue-Green Deployment
Create a deployment script that deploys with no traffic, runs health checks, then gradually shifts 10% -> 50% -> 100%.

For detailed deployment manifests and scripts, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Cloud Run deployment workflow
- Vercel serverless deployment
- AWS Lambda configuration
- Kubernetes deployment manifests
- Health check endpoint
- Blue-green deployment script

## Error Handling
| Issue | Solution |
|-------|----------|
| Secret not found | Verify secret name and permissions |
| Health check failing | Check Customer.io credentials |
| Cold start timeout | Increase memory/timeout limits |

## Resources
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Vercel Serverless Functions](https://vercel.com/docs/functions)
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

## Next Steps
After deployment, proceed to `customerio-webhooks-events` for webhook handling.
