---
name: "cursor-team-setup"
description: |
  Configure set up Cursor for teams and organizations. Triggers on "cursor team",
  "cursor organization", "cursor business", "cursor enterprise setup". Use when working with cursor team setup functionality. Trigger with phrases like "cursor team setup", "cursor setup", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---

# Cursor Team Setup

## Overview

This skill guides you through setting up Cursor for teams and organizations. It covers plan selection, member management, shared configurations, onboarding workflows, and team analytics to ensure consistent Cursor usage across your organization.

## Prerequisites

- Cursor Business or Enterprise subscription
- Admin access to Cursor organization
- Team roster and role assignments planned
- Billing and payment method configured

## Instructions

1. Create team at cursor.com/settings/team
2. Configure team plan and billing
3. Invite team members with appropriate roles
4. Set up shared .cursorrules in repository
5. Configure team analytics and usage tracking
6. Create onboarding documentation

## Output

- Configured team account with all members
- Role-based access control
- Shared configuration and standards
- Usage analytics and cost tracking
- Onboarding process documented

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Cursor Team Documentation](https://cursor.com/docs/teams)
- [Admin Dashboard Guide](https://cursor.com/docs/admin)
- [Team Best Practices](https://cursor.com/blog/teams)
