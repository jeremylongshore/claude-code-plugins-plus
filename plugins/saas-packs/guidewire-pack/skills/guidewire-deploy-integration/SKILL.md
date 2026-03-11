---
name: guidewire-deploy-integration
description: |
  Deploy Guidewire InsuranceSuite integrations to Guidewire Cloud Platform.
  Use when deploying configuration packages, managing releases,
  or implementing blue-green deployments.
  Trigger with phrases like "deploy guidewire", "guidewire cloud deployment",
  "release management", "configuration deployment", "guidewire promotion".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Guidewire Deploy Integration

## Overview
Deploy Guidewire InsuranceSuite configurations and integrations to Guidewire Cloud Platform using proper release management practices.

## Prerequisites
- Guidewire Cloud Console access
- Service account with deployment permissions
- Configuration package built and tested
- Approval for target environment

## Instructions

### Step 1: Deployment Architecture
+------------------+      +------------------+      +------------------+
### Step 2: Instructions
// build.gradle - Configuration package creation

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Deployment Architecture
- Instructions

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Package validation failed | Missing required files | Check manifest and include all files |
| Deployment timeout | Large package or slow network | Increase timeout, optimize package |
| Health check failed | Application errors | Check logs, fix issues, redeploy |
| Rollback failed | State inconsistency | Manual intervention required |

## Resources
- [Guidewire Cloud Deployment Guide](https://docs.guidewire.com/cloud/)
- [Configuration Package Reference](https://docs.guidewire.com/education/)

## Next Steps
For webhook and event handling, see `guidewire-webhooks-events`.

## Examples

**Basic usage**: Apply guidewire deploy integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize guidewire deploy integration for production environments with multiple constraints and team-specific requirements.