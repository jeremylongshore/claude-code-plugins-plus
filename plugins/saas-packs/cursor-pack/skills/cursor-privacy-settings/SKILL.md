---
name: "cursor-privacy-settings"
description: |
  Configure Cursor privacy and data handling settings. Triggers on "cursor privacy",
  "cursor data", "cursor security", "privacy mode", "cursor telemetry". Use when working with cursor privacy settings functionality. Trigger with phrases like "cursor privacy settings", "cursor settings", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---

# Cursor Privacy Settings

## Overview

This skill helps configure Cursor privacy and data handling settings. It covers privacy mode configuration, sensitive file exclusion, telemetry settings, and enterprise security controls to ensure your code and data are protected appropriately.

## Prerequisites

- Cursor IDE with admin access to settings
- Understanding of data handling requirements
- Knowledge of sensitive files in project
- Compliance requirements documented

## Instructions

1. Evaluate privacy mode needs (per project/globally)
2. Configure .cursorignore for sensitive files
3. Set up environment variables for secrets
4. Configure telemetry settings
5. Verify API key security
6. Document data handling policies

## Output

- Privacy Mode configured appropriately
- Sensitive files excluded from AI context
- Secure API key management
- Telemetry settings aligned with policy
- Documented privacy configuration

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Cursor Privacy Policy](https://cursor.com/privacy)
- [Data Handling Documentation](https://cursor.com/docs/privacy)
- [Security Best Practices](https://cursor.com/security)
