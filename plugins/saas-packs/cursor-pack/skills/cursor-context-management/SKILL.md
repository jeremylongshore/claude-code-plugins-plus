---
name: "cursor-context-management"
description: |
  Optimize context window usage in Cursor. Triggers on "cursor context",
  "context window", "context limit", "cursor memory", "context management". Use when working with cursor context management functionality. Trigger with phrases like "cursor context management", "cursor management", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---
# Cursor Context Management

## Overview

This skill helps optimize context window usage in Cursor. It covers understanding context sources, efficient @-mention strategies, conversation management, and techniques to avoid context overflow for better AI response quality.

## Prerequisites

- Cursor IDE with AI features active
- Understanding of context window limits
- Project with code files
- Familiarity with @-mention syntax

## Instructions

1. Understand your model's context limit
2. Select only relevant code before chatting
3. Use specific @-mentions for file context
4. Start new conversations for new topics
5. Monitor response quality for context issues
6. Clear context when switching tasks

## Output

- Optimized context usage
- Better AI response quality
- Faster response times
- Efficient @-mention patterns
- Clean conversation management

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Context Window Guide](https://cursor.com/docs/context)
- [Model Context Limits](https://cursor.com/docs/models)
- [Effective Prompting](https://cursor.com/docs/prompting)