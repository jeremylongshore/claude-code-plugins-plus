---
name: juicebox-data-handling
description: |
  Implement Juicebox data privacy and handling.
  Use when managing personal data, implementing GDPR compliance,
  or handling sensitive candidate information.
  Trigger with phrases like "juicebox data privacy", "juicebox GDPR",
  "juicebox PII handling", "juicebox data compliance".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Data Handling

## Overview
Implement compliant data handling practices for personal and candidate data from Juicebox.

## Prerequisites
- Understanding of applicable privacy regulations (GDPR, CCPA)
- Data classification framework
- Legal/compliance team sign-off

## Instructions
1. Step 1: Data Classification System
2. Step 2: PII Handling
3. Step 3: Retention Policies
4. Step 4: Data Subject Rights
5. Step 5: Access Logging

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Data classification system
- PII handling utilities
- Retention policy enforcement
- Data subject rights handlers

## Resources
- [Juicebox Privacy Policy](https://juicebox.ai/privacy)
- [GDPR Guidelines](https://gdpr.eu)

## Next Steps
After data handling, see `juicebox-enterprise-rbac` for access controls.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with ORM |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply juicebox data handling to a standard project setup with default configuration options.

**Advanced scenario**: Customize juicebox data handling for production environments with multiple constraints and team-specific requirements.