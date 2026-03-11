---
name: "cursor-local-dev-loop"
description: |
  Optimize local development workflow with Cursor. Triggers on "cursor workflow",
  "cursor development loop", "cursor productivity", "cursor daily workflow". Use when working with cursor local dev loop functionality. Trigger with phrases like "cursor local dev loop", "cursor loop", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---
# Cursor Local Dev Loop

## Overview

This skill helps optimize your local development workflow with Cursor IDE. It provides guidance on daily development patterns, keyboard-driven workflows, and efficient AI-assisted coding practices to maximize productivity.

## Prerequisites

- Cursor IDE installed and configured
- Project with development environment set up
- Git repository initialized
- Basic familiarity with Cursor AI features

## Instructions

1. Open project and let indexing complete
2. Review recent changes with git diff
3. Use Chat (Cmd+L) for planning and architecture
4. Use Composer (Cmd+I) for multi-file scaffolding
5. Use Tab completion for implementation
6. Use Inline Edit (Cmd+K) for quick fixes
7. Commit with AI-generated messages

## Output

- Efficient keyboard-driven workflow
- AI-assisted feature development
- Streamlined git integration
- Rapid iteration cycle

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Cursor Workflow Guide](https://cursor.com/docs/workflow)
- [Keyboard Shortcuts Reference](https://cursor.com/docs/shortcuts)
- [Developer Productivity Tips](https://cursor.com/blog/productivity)