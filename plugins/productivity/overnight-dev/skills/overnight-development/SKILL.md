---
name: overnight-development
description: Automates software development overnight using git hooks to enforce test-driven Use when appropriate context detected. Trigger with relevant phrases based on skill purpose.
version: 1.0.0
allowed-tools: "Read, Write, Edit, Grep, Glob, Bash(general:*), Bash(util:*)"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Overnight Development

## Overview

This skill automates software development overnight by leveraging Git hooks to enforce test-driven development (TDD). It ensures that all code changes are fully tested and meet specified quality standards before being committed. This approach allows Claude to work autonomously, building new features, refactoring existing code, or fixing bugs while adhering to a rigorous TDD process.

## Prerequisites

- Access to project files in ${CLAUDE_SKILL_DIR}/
- Required tools and dependencies installed
- Understanding of skill functionality
- Permissions for file operations

## Instructions

1. Identify skill activation trigger and context
2. Gather required inputs and parameters
3. Execute skill workflow systematically
4. Validate outputs meet requirements
5. Handle errors and edge cases appropriately
6. Provide clear results and next steps

## Output

- Primary deliverables based on skill purpose
- Status indicators and success metrics
- Generated files or configurations
- Reports and summaries as applicable
- Recommendations for follow-up actions

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- Official documentation for related tools
- Best practices guides
- Example use cases and templates
- Community forums and support channels
