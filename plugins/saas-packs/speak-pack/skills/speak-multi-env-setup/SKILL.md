---
name: speak-multi-env-setup
description: |
  Configure Speak across development, staging, and production environments.
  Use when setting up multi-environment deployments, configuring per-environment secrets,
  or implementing environment-specific Speak configurations.
  Trigger with phrases like "speak environments", "speak staging",
  "speak dev prod", "speak environment setup", "speak config by env".
allowed-tools: Read, Write, Edit, Bash(aws:*), Bash(gcloud:*), Bash(vault:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak Multi Env Setup

## Overview
Configure Speak across development, staging, and production environments for language learning applications.

## Prerequisites
- Separate Speak accounts or API keys per environment
- Secret management solution (Vault, AWS Secrets Manager, etc.)
- CI/CD pipeline with environment variables
- Environment detection in application

## Instructions
1. **Environment Strategy**
2. **Configuration Structure**
3. **Environment Detection**
4. **Secret Management by Environment**
5. **Environment Isolation**
6. **Feature Flags by Environment**
7. **Environment-Specific Audio Storage**
8. **Environment Health Checks**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Multi-environment config structure
- Environment detection logic
- Secure secret management
- Production safeguards enabled
- Feature flags by environment

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong environment | Missing SPEAK_ENV | Set environment variable |
| Secret not found | Wrong secret path | Verify secret manager config |
| Config merge fails | Invalid JSON | Validate config files |
| Production guard triggered | Wrong environment | Check SPEAK_ENV value |
| Feature unavailable | Wrong environment | Verify feature flags |

## Examples
### Quick Environment Check
```typescript
const config = getSpeakConfig();
console.log(`Environment: ${config.environment}`);
console.log(`API Base: ${config.baseUrl}`);
console.log(`Mock Mode: ${config.mockMode ? 'ON' : 'OFF'}`);
console.log(`Features:`, config.features);
```

## Resources
- [Speak Environments Guide](https://developer.speak.com/docs/environments)
- [12-Factor App Config](https://12factor.net/config)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)

## Next Steps
For observability setup, see `speak-observability`.