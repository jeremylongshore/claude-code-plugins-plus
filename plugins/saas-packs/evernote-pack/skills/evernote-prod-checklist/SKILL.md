---
name: evernote-prod-checklist
description: |
  Production readiness checklist for Evernote integrations.
  Use when preparing to deploy Evernote integration to production,
  or auditing production readiness.
  Trigger with phrases like "evernote production", "deploy evernote",
  "evernote go live", "production checklist evernote".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Production Checklist

## Overview
Comprehensive checklist for deploying Evernote integrations to production, covering API keys, security, performance, monitoring, and compliance.

## Prerequisites
- Completed development and testing
- Production API key approved
- Production infrastructure ready

## Instructions

1. See implementation guide for detailed steps.

2. For full implementation details and code examples, load:
3. `references/implementation-guide.md`

## Output
- Production configuration templates
- Security verification checklist
- Monitoring and alerting setup
- Health check endpoints
- Deployment verification script

## Resources
- [Evernote Developer Portal](https://dev.evernote.com/)
- [API Key Request](https://dev.evernote.com/support/)
- [Rate Limits](https://dev.evernote.com/doc/articles/rate_limits.php)

## Next Steps
For version upgrades, see `evernote-upgrade-migration`.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with Go |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply evernote prod checklist to a standard project setup with default configuration options.

**Advanced scenario**: Customize evernote prod checklist for production environments with multiple constraints and team-specific requirements.