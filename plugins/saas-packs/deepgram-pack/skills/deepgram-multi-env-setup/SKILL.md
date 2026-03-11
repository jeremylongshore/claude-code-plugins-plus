---
name: deepgram-multi-env-setup
description: |
  Configure Deepgram multi-environment setup for dev, staging, and production.
  Use when setting up environment-specific configurations, managing multiple
  Deepgram projects, or implementing environment isolation.
  Trigger with phrases like "deepgram environments", "deepgram staging",
  "deepgram dev prod", "multi-environment deepgram", "deepgram config".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Deepgram Multi-Environment Setup

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Configure isolated Deepgram environments for development, staging, and production with environment-aware config, client factory, Docker Compose profiles, Kubernetes overlays, and Terraform modules.

## Prerequisites
- Access to Deepgram Console
- Multiple Deepgram projects (one per environment)
- Secret management solution
- Container orchestration (Docker/K8s) for deployment

## Instructions

### Step 1: Create Deepgram Projects
Create separate projects in Deepgram Console for dev, staging, and production. Generate environment-specific API keys with appropriate scopes.

### Step 2: Implement Configuration Management
Define typed config per environment: model (Base for dev, Nova-2 for staging/prod), features (diarization off in dev), limits (5 concurrent dev, 100 prod), and callback URLs.

### Step 3: Build Client Factory
Create singleton Deepgram clients per environment using a Map. Auto-apply environment config (model, features) to all transcription calls.

### Step 4: Configure Docker Compose Profiles
Define `development`, `staging`, and `production` profiles with environment-specific API keys, project IDs, and port mappings. Use `x-common` anchor for shared config.

### Step 5: Set Up Kubernetes Overlays
Use Kustomize with base ConfigMap and per-environment overlays. Store API keys in SecretGenerator. Override model, concurrency, and env vars per overlay.

### Step 6: Validate All Environments
Run validation script that tests each environment: API key validity, project access, and transcription capability. Report pass/fail per environment.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Typed environment configuration
- Singleton client factory
- Docker Compose multi-profile setup
- Kubernetes Kustomize overlays
- Environment validation script
- Terraform secret management module

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong API key | Env mismatch | Validate key prefix per environment |
| Missing config | Env var not set | Throw descriptive error on startup |
| Cross-env access | Shared key | Use separate projects per environment |
| Deployment failure | Bad config | Run validation script before deploy |

## Examples

### Environment Strategy
| Environment | Model | Max Concurrent | Features |
|-------------|-------|----------------|----------|
| Development | base | 5 | Smart format only |
| Staging | nova-2 | 20 | All features |
| Production | nova-2 | 100 | All features |

### Environment Variables
```bash
# Development
DEEPGRAM_API_KEY_DEV=...
DEEPGRAM_PROJECT_ID_DEV=...

# Staging
DEEPGRAM_API_KEY_STAGING=...
DEEPGRAM_PROJECT_ID_STAGING=...

# Production
DEEPGRAM_API_KEY_PRODUCTION=...
DEEPGRAM_PROJECT_ID_PRODUCTION=...
```

## Resources
- [Deepgram Projects](https://developers.deepgram.com/docs/projects)
- [API Key Management](https://developers.deepgram.com/docs/api-key-management)
- [Environment Best Practices](https://developers.deepgram.com/docs/environments)