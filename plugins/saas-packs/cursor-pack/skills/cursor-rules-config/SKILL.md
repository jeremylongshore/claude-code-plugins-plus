---
name: "cursor-rules-config"
description: |
  Configure .cursorrules for project-specific AI behavior. Triggers on "cursorrules",
  ".cursorrules", "cursor rules", "cursor config", "cursor project settings". Use when configuring systems or services. Trigger with phrases like "cursor rules config", "cursor config", "cursor".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
---
# Cursor Rules Config

## Overview

### What is .cursorrules?
```
.cursorrules is a project-level configuration file that:
- Guides AI code generation style
- Enforces coding standards
- Provides project context
- Customizes AI behavior per project
```

## Prerequisites

- Cursor IDE installed and authenticated
- Project workspace open in Cursor
- Write access to project root directory
- Basic understanding of YAML syntax

## Instructions

1. Navigate to your project root directory
2. Create a new file named `.cursorrules`
3. Add project metadata (name, language, framework)
4. Define coding rules and conventions
5. Include examples of preferred patterns
6. Save the file and test with Cursor AI

## Output

- `.cursorrules` file at project root
- Customized AI code generation behavior
- Consistent code style across AI suggestions
- Project-specific context for Cursor AI

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Cursor Documentation](https://cursor.com/docs)
- [YAML Syntax Guide](https://yaml.org/spec/)
- [Cursor Community Discord](https://discord.gg/cursor)