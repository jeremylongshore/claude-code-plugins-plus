---
name: klingai-compliance-review
description: |
  Execute conduct compliance reviews for Kling AI integrations. Use when preparing for audits,
  ensuring regulatory compliance, or reviewing security posture. Trigger with phrases like
  'klingai compliance', 'kling ai audit prep', 'klingai security review', 'video generation compliance'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Klingai Compliance Review

## Overview

This skill provides compliance review frameworks, security checklists, and audit preparation guides for Kling AI integrations to meet regulatory and organizational requirements.

## Prerequisites

- Kling AI integration in production
- Understanding of applicable regulations
- Access to system documentation

## Instructions

Follow these steps for compliance review:

1. **Identify Requirements**: Determine applicable regulations
2. **Assess Current State**: Audit existing implementation
3. **Gap Analysis**: Identify compliance gaps
4. **Remediate Issues**: Fix identified problems
5. **Document Evidence**: Prepare audit materials

## Output

Successful execution produces:
- Compliance assessment report
- Gap analysis findings
- Prioritized remediation plan
- Audit-ready documentation

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [SOC 2 Compliance](https://www.aicpa.org/soc)
- [GDPR Requirements](https://gdpr.eu/)
- [NIST AI Risk Management](https://www.nist.gov/itl/ai-risk-management-framework)
- [AI Ethics Guidelines](https://www.oecd.ai/en/ai-principles)