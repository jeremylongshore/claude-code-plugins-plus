---
name: customerio-multi-env-setup
description: |
  Configure Customer.io multi-environment setup.
  Use when setting up development, staging, and production
  environments with proper isolation.
  Trigger with phrases like "customer.io environments", "customer.io staging",
  "customer.io dev prod", "customer.io workspace".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Customer.io Multi-Environment Setup

## Overview
Configure isolated Customer.io environments for development, staging, and production with proper data separation and configuration management.

## Prerequisites
- Customer.io account with multiple workspaces
- Environment variable management system
- CI/CD pipeline configured

## Instructions

### Step 1: Create Separate Workspaces
Create workspaces in Customer.io for each environment (`[app]-dev`, `[app]-staging`, `[app]-prod`), generate API keys, and store credentials securely.

### Step 2: Build Environment Configuration
Create a typed config module that loads credentials per environment with validation, dry-run support, log level control, and event prefixing.

### Step 3: Create Environment-Aware Client
Build a client wrapper that automatically selects the correct workspace, adds environment tags to attributes, and supports dry-run mode for development.

### Step 4: Configure Kubernetes Overlays
Use Kustomize overlays for per-environment ConfigMaps controlling region, dry-run mode, and log levels.

### Step 5: Set Up Secrets Management
Use ExternalSecrets or similar to pull Customer.io credentials from your secrets manager per environment.

### Step 6: Configure CI/CD Promotion
Create workflow dispatch for promoting between environments with credential verification and smoke tests.

### Step 7: Verify Data Isolation
Run isolation verification scripts that create test users in each workspace and confirm no cross-environment data leakage.

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Per-environment workspace configuration
- Typed environment config with validation
- Environment-aware Customer.io client
- Kubernetes ConfigMap overlays
- ExternalSecrets for credential management
- CI/CD promotion workflow
- Data isolation verification script

## Error Handling
| Issue | Solution |
|-------|----------|
| Wrong environment data | Verify workspace credentials match env |
| Cross-env pollution | Use distinct user ID prefixes per env |
| Missing secrets | Check secret manager configuration |

## Resources
- [Customer.io Workspaces](https://customer.io/docs/workspaces/)
- [API Environments](https://customer.io/docs/api/track/)

## Next Steps
After multi-env setup, proceed to `customerio-observability` for monitoring.

## Examples

**Basic usage**: Apply customerio multi env setup to a standard project setup with default configuration options.

**Advanced scenario**: Customize customerio multi env setup for production environments with multiple constraints and team-specific requirements.