---
name: "cursor-ai-chat"
description: |
  Manage master Cursor AI chat interface for code assistance. Triggers on "cursor chat",
  "cursor ai chat", "ask cursor", "cursor conversation", "chat with cursor". Use when working with cursor ai chat functionality. Trigger with phrases like "cursor ai chat", "cursor chat", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---
# Cursor Ai Chat

## Overview

This skill helps you master the Cursor AI chat interface for code assistance. It covers effective prompting patterns, context management with @-mentions, model selection, and techniques for getting the best responses from AI.

## Prerequisites

- Cursor IDE installed and authenticated
- Project workspace with code files
- Understanding of @-mention syntax
- Basic familiarity with AI prompting

## Instructions

1. Open AI Chat panel (Cmd+L or Ctrl+L)
2. Select relevant code before asking questions
3. Use @-mentions to add file context
4. Ask specific, clear questions
5. Review and apply suggested code
6. Use multi-turn conversations for iterative work

## Output

- Code explanations and documentation
- Generated code snippets
- Debugging assistance
- Refactoring suggestions
- Code review feedback

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Cursor Chat Documentation](https://cursor.com/docs/chat)
- [Effective Prompting Guide](https://cursor.com/docs/prompting)
- [Context Management Tips](https://cursor.com/docs/context)