---
name: apollo-multi-env-setup
description: |
  Configure Apollo.io multi-environment setup.
  Use when setting up development, staging, and production environments,
  or managing multiple Apollo configurations.
  Trigger with phrases like "apollo environments", "apollo staging",
  "apollo dev prod", "apollo multi-tenant", "apollo env config".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Multi-Environment Setup

## Overview
Configure Apollo.io for multiple environments (development, staging, production) with proper isolation, configuration management, and deployment strategies.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions
Follow these high-level steps to implement apollo-multi-env-setup:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-multi-env-setup/references/implementation-guide.md)`

## Output
- Environment-specific configurations
- Kubernetes ConfigMaps and Secrets
- Environment-aware client
- Feature flags per environment
- Environment promotion scripts

## Error Handling
| Issue | Resolution |
|-------|------------|
| Wrong environment | Check NODE_ENV variable |
| Missing API key | Verify secrets configuration |
| Feature disabled | Check environment config |
| Rate limit mismatch | Verify config values |

## Resources
- [12-Factor App Configuration](https://12factor.net/config)
- [Kubernetes ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [External Secrets Operator](https://external-secrets.io/)

## Next Steps
Proceed to `apollo-observability` for monitoring setup.

## Examples

**Basic usage**: Apply apollo multi env setup to a standard project setup with default configuration options.

**Advanced scenario**: Customize apollo multi env setup for production environments with multiple constraints and team-specific requirements.