---
name: klingai-audit-logging
description: |
  Implement comprehensive audit logging for Kling AI operations. Use when tracking API usage,
  compliance requirements, or security audits. Trigger with phrases like 'klingai audit',
  'kling ai logging', 'klingai compliance log', 'video generation audit trail'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Klingai Audit Logging

## Overview

This skill demonstrates implementing comprehensive audit logging for Kling AI operations including API calls, user actions, security events, and compliance-ready logs.

## Prerequisites

- Kling AI API key configured
- Log storage (file, database, or cloud logging)
- Python 3.8+

## Instructions

Follow these steps for audit logging:

1. **Define Events**: Identify what to log
2. **Create Logger**: Implement logging infrastructure
3. **Capture Context**: Include all relevant metadata
4. **Store Securely**: Use tamper-evident storage
5. **Enable Search**: Make logs queryable

## Output

Successful execution produces:
- Timestamped audit events
- Tamper-evident checksums
- User activity summaries
- Compliance-ready logs

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Audit Logging Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
- [SOC 2 Logging Requirements](https://www.aicpa.org/soc)
- [GDPR Audit Requirements](https://gdpr.eu/article-30-records-of-processing-activities/)
