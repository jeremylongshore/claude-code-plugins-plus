---
name: klingai-prod-checklist
description: |
  Execute pre-launch production readiness checklist for Kling AI. Use when preparing to deploy video
  generation to production. Trigger with phrases like 'klingai production', 'kling ai go-live',
  'klingai launch checklist', 'deploy klingai'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Klingai Prod Checklist

## Overview

This skill provides a comprehensive checklist covering security, monitoring, error handling, and operational readiness for production Kling AI deployments.

## Prerequisites

- Working Kling AI integration
- Production infrastructure ready
- Monitoring systems configured

## Instructions

Follow these steps to prepare for production:

1. **Security Review**: Audit credentials and access
2. **Error Handling**: Verify all error paths
3. **Monitoring Setup**: Configure observability
4. **Performance Testing**: Validate under load
5. **Documentation**: Complete runbooks

## Output

Successful execution produces:
- Comprehensive readiness report
- Pass/fail status for each check
- Clear action items for failures
- Production approval status

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Kling AI Best Practices](https://docs.klingai.com/best-practices)
- [Production Deployment Guide](https://docs.klingai.com/deployment)
- [SRE Checklist](https://sre.google/sre-book/service-best-practices/)