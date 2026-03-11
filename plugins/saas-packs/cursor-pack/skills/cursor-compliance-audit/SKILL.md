---
name: "cursor-compliance-audit"
description: |
  Execute compliance and security auditing for Cursor usage. Triggers on "cursor compliance",
  "cursor audit", "cursor security review", "cursor soc2", "cursor gdpr". Use when analyzing or auditing cursor compliance audit. Trigger with phrases like "cursor compliance audit", "cursor audit", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---

# Cursor Compliance Audit

## Overview

This skill helps execute compliance and security auditing for Cursor usage. It covers SOC 2, GDPR, and HIPAA considerations with audit checklists, evidence collection procedures, and remediation guidance to maintain regulatory compliance.

## Prerequisites

- Cursor Business or Enterprise subscription
- Understanding of compliance requirements (SOC 2, GDPR, HIPAA)
- Admin access to Cursor organization
- Audit tools and documentation templates

## Instructions

1. Review Cursor's compliance certifications
2. Conduct access control audit
3. Verify data protection settings
4. Document configuration and policies
5. Run security scanning tools
6. Generate audit report and remediation plan

## Output

- Compliance audit report
- Access control documentation
- Data protection verification
- Remediation plan for findings
- Stakeholder communication

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Cursor Security Page](https://cursor.com/security)
- [Cursor Privacy Policy](https://cursor.com/privacy)
- [SOC 2 Documentation](https://cursor.com/docs/compliance)
- [GDPR Compliance Guide](https://cursor.com/docs/gdpr)
