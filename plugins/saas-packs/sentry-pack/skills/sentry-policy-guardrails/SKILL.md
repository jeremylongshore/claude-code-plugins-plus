---
name: sentry-policy-guardrails
description: |
  Implement governance and policy guardrails for Sentry.
  Use when enforcing organizational standards, compliance rules,
  or standardizing Sentry usage across teams.
  Trigger with phrases like "sentry governance", "sentry standards",
  "sentry policy", "enforce sentry configuration".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Sentry Policy Guardrails

## Prerequisites

- Organization-wide standards documented
- Team structure defined
- Compliance requirements identified
- Shared configuration package repository

## Instructions

1. Create shared Sentry configuration package with organization defaults
2. Define enforced settings that cannot be overridden (sendDefaultPii, sample rates)
3. Implement mandatory PII scrubbing in beforeSend hook
4. Add environment enforcement to block test data in production
5. Create standard alert policy templates with required rules
6. Implement project naming validation following team-service-environment pattern
7. Build configuration audit script to check compliance across projects
8. Set up compliance dashboard with metrics reporting
9. Document policy requirements and share with all teams
10. Enforce shared config package usage in CI/CD pipelines

## Output
- Shared Sentry configuration package
- Enforced organization defaults
- Alert policy templates
- Project naming validation
- Compliance audit reports

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Sentry Organization Settings](https://docs.sentry.io/product/accounts/getting-started/)
- [Sentry API](https://docs.sentry.io/api/)
