---
name: sentry-known-pitfalls
description: |
  Execute common Sentry pitfalls and how to avoid them.
  Use when troubleshooting Sentry issues, reviewing configurations,
  or preventing common mistakes.
  Trigger with phrases like "sentry mistakes", "sentry pitfalls",
  "sentry common issues", "sentry anti-patterns".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Sentry Known Pitfalls

## Prerequisites

- Existing Sentry implementation to review
- Access to SDK configuration
- Understanding of current error patterns
- Codebase access for fixes

## Instructions

1. Verify SDK initialization happens before app starts
2. Check for single initialization point (no multiple init calls)
3. Use framework-specific SDK package for your framework
4. Ensure Error objects are captured (not strings)
5. Verify beforeSend returns event or null explicitly
6. Check DSN is in environment variables (not hardcoded)
7. Review sample rates for production appropriateness
8. Verify all transactions call finish() in try/finally
9. Check source map URL prefix matches actual URLs
10. Review alert configuration for threshold-based rules (avoid alert fatigue)

## Output
- Pitfalls identified in current setup
- Fixes applied for each issue
- Configuration validated
- Best practices checklist completed

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Sentry Best Practices](https://docs.sentry.io/product/issues/best-practices/)
- [Troubleshooting Guide](https://docs.sentry.io/platforms/javascript/troubleshooting/)
