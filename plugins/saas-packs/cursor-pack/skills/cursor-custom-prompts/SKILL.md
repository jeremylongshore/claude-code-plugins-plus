---
name: "cursor-custom-prompts"
description: |
  Create effective custom prompts for Cursor AI. Triggers on "cursor prompts",
  "prompt engineering cursor", "better cursor prompts", "cursor instructions". Use when working with cursor custom prompts functionality. Trigger with phrases like "cursor custom prompts", "cursor prompts", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---

# Cursor Custom Prompts

## Overview

This skill helps you create effective custom prompts for Cursor AI. It covers prompt engineering fundamentals, domain-specific templates, advanced techniques like chain-of-thought prompting, and best practices for consistent, high-quality AI responses.

## Prerequisites

- Cursor IDE with Chat or Composer
- Understanding of prompt engineering basics
- Project with existing patterns to reference
- .cursorrules file for persistent prompts

## Instructions

1. Structure prompt with context, task, constraints
2. Include specific requirements and formats
3. Reference existing patterns with @-mentions
4. Start with simple prompt, iterate for complexity
5. Store effective prompts in .cursorrules
6. Refine based on output quality

## Output

- Effective prompt templates
- Consistent AI output quality
- Reusable prompt patterns
- Project-specific prompt library

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Prompt Engineering Guide](https://cursor.com/docs/prompting)
- [.cursorrules Reference](https://cursor.com/docs/rules)
- [Cursor Community Prompts](https://forum.cursor.com/c/prompts)
