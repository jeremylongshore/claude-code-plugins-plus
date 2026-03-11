---
name: "windsurf-cascade-context"
description: |
  Manage Cascade context window and memory for complex projects. Activate when users mention
  "cascade context", "ai memory", "context management", "large codebase navigation",
  or "multi-session development". Handles context optimization and persistence. Use when working with windsurf cascade context functionality. Trigger with phrases like "windsurf cascade context", "windsurf context", "windsurf".
allowed-tools: Read,Write,Edit,Grep,Glob
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---

# Windsurf Cascade Context

## Overview

This skill enables advanced context management for Cascade AI in large-scale projects. It covers context prioritization, memory persistence across sessions, and optimization strategies for codebases with hundreds or thousands of files. Proper context management ensures Cascade maintains accurate understanding of your project architecture and conventions during extended development sessions.

## Prerequisites

- Windsurf IDE with Cascade enabled
- Large codebase (50+ files)
- Project documentation available
- Understanding of project architecture
- Clear identification of critical code paths

## Instructions

1. **Map Project Structure**
2. **Configure Context Priorities**
3. **Create Context Documentation**
4. **Optimize for Workflow**
5. **Monitor and Refine**


See `${CLAUDE_SKILL_DIR}/references/implementation.md` for detailed implementation guide.

## Output

- Optimized context configuration
- Project context documentation
- Module index for navigation
- Session state persistence

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Windsurf Context Management](https://docs.windsurf.ai/features/context)
- [Large Codebase Best Practices](https://docs.windsurf.ai/guides/large-codebases)
- [Memory Persistence Configuration](https://docs.windsurf.ai/features/memory)
