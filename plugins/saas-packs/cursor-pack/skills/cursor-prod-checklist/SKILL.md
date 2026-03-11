---
name: "cursor-prod-checklist"
description: |
  Execute production readiness checklist for Cursor IDE setup. Triggers on "cursor production",
  "cursor ready", "cursor checklist", "optimize cursor setup". Use when working with cursor prod checklist functionality. Trigger with phrases like "cursor prod checklist", "cursor checklist", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---

# Cursor Prod Checklist

## Overview

This skill provides a comprehensive production readiness checklist for Cursor IDE setup. It covers authentication, configuration, security, performance optimization, and team standards to ensure your Cursor environment is properly configured for professional use.

## Prerequisites

- Cursor IDE installed
- Project workspace ready for configuration
- Team alignment on coding standards
- Understanding of Cursor features and settings

## Instructions

1. Complete authentication and licensing setup
2. Create and configure .cursorrules file
3. Set up .cursorignore for indexing exclusions
4. Configure security and privacy settings
5. Verify all AI features working correctly
6. Document setup for team onboarding

## Output

- Production-ready Cursor configuration
- Optimized AI settings for project
- Security-compliant setup
- Documented team standards
- Maintenance schedule established

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Cursor Setup Guide](https://cursor.com/docs/setup)
- [Enterprise Configuration](https://cursor.com/docs/enterprise)
- [Security Best Practices](https://cursor.com/security)
