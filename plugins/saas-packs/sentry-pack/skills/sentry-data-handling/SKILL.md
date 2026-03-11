---
name: sentry-data-handling
description: |
  Manage sensitive data properly in Sentry.
  Use when configuring PII scrubbing, data retention,
  GDPR compliance, or data security settings.
  Trigger with phrases like "sentry pii", "sentry gdpr",
  "sentry data privacy", "scrub sensitive data sentry".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Sentry Data Handling

## Prerequisites

- Sentry project with admin access
- Compliance requirements documented (GDPR, HIPAA, PCI-DSS)
- List of sensitive data patterns to scrub
- Understanding of data retention requirements

## Instructions

1. Enable server-side data scrubbing in Project Settings > Security & Privacy
2. Configure client-side scrubbing in beforeSend hook for PII fields
3. Add custom scrubbing rules for credit cards, SSNs, and email patterns
4. Disable sendDefaultPii in SDK configuration
5. Configure IP address anonymization or disable IP collection
6. Set appropriate data retention period in organization settings
7. Implement user consent handling for GDPR compliance
8. Document right to erasure process with API deletion endpoint
9. Run tests to verify sensitive data is properly scrubbed
10. Complete compliance checklist for applicable regulations

## Output
- PII scrubbing rules configured
- GDPR compliance documentation
- Data retention policies implemented
- User consent handling code

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Sentry Data Privacy](https://docs.sentry.io/product/data-management-settings/data-privacy/)
- [GDPR Compliance](https://sentry.io/legal/gdpr/)
- [Data Scrubbing](https://docs.sentry.io/product/data-management-settings/scrubbing/)

## Overview

Manage sensitive data properly in Sentry.