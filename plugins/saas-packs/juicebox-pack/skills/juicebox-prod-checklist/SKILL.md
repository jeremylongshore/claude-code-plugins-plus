---
name: juicebox-prod-checklist
description: |
  Execute Juicebox production deployment checklist.
  Use when preparing for production launch, validating deployment readiness,
  or performing pre-launch reviews.
  Trigger with phrases like "juicebox production", "deploy juicebox prod",
  "juicebox launch checklist", "juicebox go-live".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Production Checklist

## Overview
Complete production readiness checklist for Juicebox integration deployment.

## Prerequisites
- Development and staging testing complete
- Production environment provisioned
- Monitoring infrastructure ready

## Instructions
1. Production Readiness Checklist
2. Validation Scripts
3. Go-Live Checklist
4. Day-of-Launch Checklist

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Resources
- [Production Best Practices](https://juicebox.ai/docs/production)
- [Status Page](https://status.juicebox.ai)

## Next Steps
After production launch, see `juicebox-upgrade-migration` for SDK updates.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [deployment implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with deployment |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply juicebox prod checklist to a standard project setup with default configuration options.

**Advanced scenario**: Customize juicebox prod checklist for production environments with multiple constraints and team-specific requirements.