---
name: apollo-deploy-integration
description: |
  Deploy Apollo.io integrations to production.
  Use when deploying Apollo integrations, configuring production environments,
  or setting up deployment pipelines.
  Trigger with phrases like "deploy apollo", "apollo production deploy",
  "apollo deployment pipeline", "apollo to production".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Deploy Integration

## Overview
Deploy Apollo.io integrations to production environments with proper configuration, health checks, and rollback procedures.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions
Follow these high-level steps to implement apollo-deploy-integration:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-deploy-integration/references/implementation-guide.md)`

## Output
- Platform-specific deployment configs (Vercel, GCP, AWS, K8s)
- Health check endpoints
- Blue-green deployment workflow
- Pre-deployment validation
- Environment configuration

## Error Handling
| Issue | Resolution |
|-------|------------|
| Secret not found | Verify secret configuration |
| Health check fails | Check Apollo connectivity |
| Deployment timeout | Increase timeout, check resources |
| Traffic not switching | Verify service selector |

## Resources
- [Vercel Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)
- [Google Cloud Secret Manager](https://cloud.google.com/secret-manager)
- [AWS Systems Manager](https://docs.aws.amazon.com/systems-manager/)
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)

## Next Steps
Proceed to `apollo-webhooks-events` for webhook implementation.

## Examples

**Basic usage**: Apply apollo deploy integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize apollo deploy integration for production environments with multiple constraints and team-specific requirements.