---
name: maintainx-deploy-integration
description: |
  Deploy MaintainX integrations to production environments.
  Use when deploying to cloud platforms, configuring production environments,
  or automating deployment pipelines for MaintainX integrations.
  Trigger with phrases like "deploy maintainx", "maintainx deployment",
  "maintainx cloud deploy", "maintainx kubernetes", "maintainx docker".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(docker:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Deploy Integration

## Overview
Deploy MaintainX integrations to production environments with Docker, Kubernetes, and cloud platform configurations.

## Prerequisites
- MaintainX integration tested and ready
- Docker installed
- Cloud platform account (GCP, AWS, or Azure)
- Kubernetes cluster (optional)

## Instructions
Follow these high-level steps to implement maintainx-deploy-integration:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/maintainx-pack/skills/maintainx-deploy-integration/references/implementation-guide.md)`

## Output
- Dockerfile and docker-compose configured
- Kubernetes manifests created
- Cloud Run deployment configured
- Health check endpoints implemented
- CI/CD deploy workflow ready

## Error Handling
| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Verify API key in environment variables |
| 429 Rate Limited | Implement exponential backoff, reduce request frequency |
| 500 Server Error | Retry with backoff, check MaintainX status page |

## Resources
- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Google Cloud Run](https://cloud.google.com/run/docs)
- [AWS Lambda](https://docs.aws.amazon.com/lambda/)

## Next Steps
For webhook integration, see `maintainx-webhooks-events`.

## Examples

**Basic usage**: Apply maintainx deploy integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize maintainx deploy integration for production environments with multiple constraints and team-specific requirements.