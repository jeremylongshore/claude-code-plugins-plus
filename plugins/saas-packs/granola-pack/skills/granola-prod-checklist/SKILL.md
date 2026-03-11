---
name: granola-prod-checklist
description: |
  Production readiness checklist for Granola deployment.
  Use when preparing for team rollout, enterprise deployment,
  or ensuring Granola is properly configured for production use.
  Trigger with phrases like "granola production", "granola rollout",
  "granola deployment", "granola checklist", "granola enterprise setup".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Granola Production Checklist

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Comprehensive checklist for deploying Granola in a production/enterprise environment covering security, integrations, training, and go-live procedures.

## Prerequisites
- Appropriate Granola plan selected (Pro/Business/Enterprise)
- Sufficient seat licenses for team
- Admin access to Granola workspace

## Instructions

### Step 1: Account & Licensing
- [ ] Plan selected and billing verified
- [ ] Contract/Terms reviewed and signed
- [ ] Enterprise agreement in place (if applicable)

### Step 2: Security Configuration
Configure SSO, 2FA, password policies, IP allowlisting, data residency, and audit logging.

### Step 3: Integration Setup
Connect calendar (Google/Outlook), communication (Slack/Teams), documentation (Notion/Confluence), and optionally CRM and task management tools.

### Step 4: Workspace & User Configuration
Set workspace branding, sharing permissions, data retention, templates, user roles, and permission groups.

### Step 5: Run Pilot Program
Select 5-10 pilot users, define success metrics, run for 2 weeks, collect daily feedback, and address issues before full rollout.

### Step 6: Go-Live
Execute launch day checklist: send welcome emails, enable access, monitor adoption, staff support channel. Track metrics daily for first week.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete checklists, technical requirements, network configuration, training plans, and success metrics.

## Output
- Security fully configured (SSO, 2FA, audit logging)
- Integrations connected and tested
- Pilot completed with feedback incorporated
- Team onboarded and recording meetings

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| SSO login failure | Misconfigured SAML/OIDC | Verify SSO settings with identity provider |
| Calendar not syncing | OAuth token expired | Reconnect calendar integration |
| Low adoption | Insufficient training | Schedule additional training sessions |
| Recording not starting | Missing permissions | Verify microphone and calendar permissions |

## Examples

### Quick Adoption Check (Week 1)
| Metric | Target | Actual |
|--------|--------|--------|
| User activation | 80% | ___ |
| Meetings captured | 70% | ___ |
| Support tickets | <5% users | ___ |

## Resources
- [Granola Admin Guide](https://granola.ai/admin)
- [Enterprise Setup](https://granola.ai/enterprise)
- [Status Page](https://status.granola.ai)

## Next Steps
Proceed to `granola-upgrade-migration` for version upgrade guidance.