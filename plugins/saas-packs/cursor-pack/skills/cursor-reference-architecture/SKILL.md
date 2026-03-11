---
name: "cursor-reference-architecture"
description: |
  Execute reference architecture patterns for Cursor IDE projects. Triggers on "cursor architecture",
  "cursor project structure", "cursor best practices", "cursor team setup". Use when working with cursor reference architecture functionality. Trigger with phrases like "cursor reference architecture", "cursor architecture", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---
# Cursor Reference Architecture

## Overview

This skill provides reference architecture patterns for Cursor IDE projects. It covers project structure conventions, configuration file architecture, team workflows, monorepo patterns, and security considerations for enterprise-ready setups.

## Prerequisites

- Project with defined architecture patterns
- Understanding of project structure conventions
- Team alignment on coding standards
- Cursor IDE configured for team use

## Instructions

1. Choose project structure (feature-based or layer-based)
2. Create comprehensive .cursorrules file
3. Configure .cursorignore for indexing
4. Set up workspace settings for team
5. Document architecture decisions
6. Create onboarding documentation

## Output

- Well-organized project structure
- Comprehensive .cursorrules configuration
- Team-aligned configuration files
- Documented architecture patterns
- AI-friendly codebase

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Cursor Architecture Guide](https://cursor.com/docs/architecture)
- [Project Structure Best Practices](https://cursor.com/docs/structure)
- [Team Configuration Guide](https://cursor.com/docs/teams)