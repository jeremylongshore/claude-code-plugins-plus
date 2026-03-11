---
name: sentry-security-basics
description: |
  Configure Sentry security settings and data protection.
  Use when setting up data scrubbing, managing sensitive data,
  or configuring security policies.
  Trigger with phrases like "sentry security", "sentry PII",
  "sentry data scrubbing", "secure sentry".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Sentry Security Basics

## Prerequisites

- Security requirements documented
- Compliance standards identified (GDPR, SOC 2, HIPAA)
- Sensitive data patterns known
- Access control needs defined

## Instructions

1. Enable server-side data scrubbing in project settings
2. Configure client-side scrubbing in beforeSend for user data and request bodies
3. Add sensitive field patterns for passwords, tokens, and API keys
4. Store DSN in environment variables, never hardcode
5. Set sendDefaultPii to false in SDK configuration
6. Configure team permissions with principle of least privilege
7. Create API tokens with minimal required scopes
8. Rotate DSN keys and disable old ones after deployment
9. Enable audit logging for compliance tracking
10. Complete security checklist and document compliance status

## Output
- Data scrubbing configured
- DSN secured in environment variables
- Access controls implemented
- Security checklist completed

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Sentry Security](https://docs.sentry.io/product/security/)
- [Data Privacy](https://docs.sentry.io/platforms/javascript/data-management/)
