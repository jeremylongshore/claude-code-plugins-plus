---
name: clerk-data-handling
description: |
  Handle user data, privacy, and GDPR compliance with Clerk.
  Use when implementing data export, user deletion,
  or privacy compliance features.
  Trigger with phrases like "clerk user data", "clerk GDPR",
  "clerk privacy", "clerk data export", "clerk delete user".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Clerk Data Handling

## Overview
Manage user data, implement privacy features, and ensure compliance with regulations.

## Prerequisites
- Clerk integration working
- Understanding of GDPR/CCPA requirements
- Database with user-related data

## Instructions
- Step 1: User Data Export
- Step 2: User Deletion (Right to be Forgotten)
- Step 3: Data Retention Policies
- Step 4: Consent Management
- Step 5: GDPR API Endpoints
- Step 6: Audit Logging

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Data export functionality
- User deletion capability
- Consent management
- Audit logging

## Error Handling
| Scenario | Action |
|----------|--------|
| Partial deletion | Retry failed services, log for manual review |
| Export timeout | Queue export, email when complete |
| Consent sync fail | Retry with exponential backoff |

## Resources
- [GDPR Requirements](https://gdpr.eu)
- [CCPA Requirements](https://oag.ca.gov/privacy/ccpa)
- [Clerk Privacy](https://clerk.com/legal/privacy)

## Next Steps
Proceed to `clerk-enterprise-rbac` for enterprise SSO and RBAC.
