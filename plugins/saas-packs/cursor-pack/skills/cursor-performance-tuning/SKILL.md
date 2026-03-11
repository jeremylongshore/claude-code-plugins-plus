---
name: "cursor-performance-tuning"
description: |
  Optimize Cursor IDE performance. Triggers on "cursor performance",
  "cursor slow", "cursor optimization", "cursor memory", "speed up cursor". Use when working with cursor performance tuning functionality. Trigger with phrases like "cursor performance tuning", "cursor tuning", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---
# Cursor Performance Tuning

## Overview

This skill helps optimize Cursor IDE performance. It covers performance diagnostics, editor optimization settings, extension management, AI feature tuning, and indexing configuration to ensure a fast and responsive development experience.

## Prerequisites

- Cursor IDE installed
- Access to Cursor settings
- System monitoring tools available
- Understanding of extensions and processes

## Instructions

1. Use Process Explorer to identify bottlenecks
2. Disable visual features for performance gains
3. Configure file watcher exclusions
4. Audit and disable heavy extensions
5. Optimize AI feature settings
6. Set up aggressive .cursorignore

## Output

- Improved editor performance
- Reduced CPU and memory usage
- Faster AI completions
- Optimized indexing configuration

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Cursor Performance Guide](https://cursor.com/docs/performance)
- [VS Code Performance](https://code.visualstudio.com/docs/editor/editingevolved#_performance)
- [Extension Performance Tips](https://cursor.com/docs/extensions)