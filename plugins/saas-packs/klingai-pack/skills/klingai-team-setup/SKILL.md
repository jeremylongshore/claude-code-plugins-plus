---
name: klingai-team-setup
description: |
  Configure Kling AI for team and organization use. Use when setting up shared access,
  managing team API keys, or organizing projects. Trigger with phrases like 'klingai team',
  'kling ai organization', 'klingai multi-user', 'shared klingai access'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Klingai Team Setup

## Overview

This skill guides you through setting up Kling AI for teams, including API key management, access controls, project organization, and role-based permissions.

## Prerequisites

- Kling AI account with team/enterprise plan
- Admin access to organization settings
- Understanding of RBAC concepts

## Instructions

Follow these steps for team setup:

1. **Create Organization**: Set up team organization
2. **Generate API Keys**: Create per-team or per-project keys
3. **Define Roles**: Set up role-based access
4. **Configure Quotas**: Assign usage limits
5. **Monitor Usage**: Track team consumption

## Output

Successful execution produces:
- Team configuration file
- Role-based access controls
- Project-specific API keys
- Permission enforcement

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Kling AI Teams](https://docs.klingai.com/teams)
- [RBAC Patterns](https://auth0.com/docs/manage-users/access-control/rbac)
- [API Key Management](https://docs.klingai.com/api-keys)