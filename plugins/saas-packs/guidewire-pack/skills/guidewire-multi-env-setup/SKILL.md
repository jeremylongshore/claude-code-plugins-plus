---
name: guidewire-multi-env-setup
description: |
  Configure multi-environment setup for Guidewire InsuranceSuite including development,
  staging, and production environments with proper isolation and promotion workflows.
  Trigger with phrases like "guidewire environments", "multi-environment",
  "dev staging production", "environment configuration", "environment promotion". Use when working with guidewire multi env setup.
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Guidewire Multi-Environment Setup

## Overview

Configure and manage multiple Guidewire InsuranceSuite environments with proper isolation, configuration management, and promotion workflows.

## Prerequisites

- Guidewire Cloud Console access for all environments
- Understanding of environment promotion workflows
- Git-based configuration management
- CI/CD pipeline infrastructure

## Instructions

### Step 1: Environment Configuration Structure

```
config/environments/
├── base/          # Shared configuration
├── dev/           # Dev overrides + encrypted secrets
├── qa/            # QA overrides + encrypted secrets
├── uat/           # UAT overrides + encrypted secrets
└── prod/          # Prod overrides + encrypted secrets
```

### Step 2: Environment-Specific Properties

Each environment overrides base properties for tenant ID, Hub URL, API base URL, logging levels, feature flags, and integration endpoints. Dev uses mocked integrations; prod uses real endpoints.

### Step 3: Gradle Multi-Environment Build

Configure `build.gradle` to load properties based on `-Penv=` flag. Base properties load first, then environment-specific ones override.

### Step 4: Environment Manager

Build a TypeScript `EnvironmentManager` that resolves config by environment name, provides feature flags, and constructs environment-aware API clients with correct credentials.

### Step 5: Secrets Management

Use cloud secret managers (GCP Secret Manager, AWS Secrets Manager) to store per-environment credentials. Implement secret rotation without downtime.

### Step 6: Environment Promotion Workflow

Enforce promotion paths: DEV -> QA -> UAT -> PROD. Require change tickets for production. Run pre-promotion health checks and post-promotion smoke tests.

For detailed code implementations (properties files, Gradle config, TypeScript managers, promotion workflow), load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Environment Matrix

| Aspect | DEV | QA | UAT | PROD |
|--------|-----|-----|-----|------|
| Purpose | Development | Integration Testing | Acceptance | Live |
| Data | Synthetic | Anonymized | Prod-like | Production |
| Integrations | Mocked | Sandbox | Sandbox | Production |
| Access | Developers | QA Team | Business Users | Restricted |
| Refresh Cycle | On-demand | Weekly | Monthly | N/A |
| Monitoring | Basic | Standard | Standard | Comprehensive |

## Output

- Environment configuration structure
- Gradle multi-environment build
- Secrets management integration
- Promotion workflow automation
- Health monitoring dashboard

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong environment config | Missing `-Penv` flag | Default to dev, validate at startup |
| Secret not found | Wrong path or permissions | Verify IAM roles and secret names |
| Promotion blocked | Failed health check | Fix source environment issues first |
| Config drift | Manual changes | Use Git-based config only |

## Resources

- [Guidewire Cloud Console](https://gcc.guidewire.com/)
- [Environment Management](https://docs.guidewire.com/cloud/)

## Next Steps

For monitoring and observability, see `guidewire-observability`.

## Examples

**Basic usage**: Apply guidewire multi env setup to a standard project setup with default configuration options.

**Advanced scenario**: Customize guidewire multi env setup for production environments with multiple constraints and team-specific requirements.