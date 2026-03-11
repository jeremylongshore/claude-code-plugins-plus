---
name: klingai-known-pitfalls
description: |
  Manage avoid common mistakes when using Kling AI. Use when troubleshooting issues or learning
  best practices to prevent problems. Trigger with phrases like 'klingai pitfalls',
  'kling ai mistakes', 'klingai gotchas', 'klingai best practices'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Klingai Known Pitfalls

## Overview

This skill documents common mistakes, gotchas, and pitfalls when working with Kling AI, along with solutions and best practices to avoid them.

## Prerequisites

- Basic Kling AI usage experience
- Encountered issues to troubleshoot
- Desire to improve implementation

## Instructions

Follow these steps to avoid pitfalls:

1. **Review Common Issues**: Understand frequent problems
2. **Apply Best Practices**: Implement recommendations
3. **Test Thoroughly**: Validate implementations
4. **Monitor Continuously**: Watch for new issues
5. **Update Regularly**: Keep up with API changes

## Output

Successful execution produces:
- Robust error handling
- Proper async patterns
- Secure credential management
- Cost-controlled generation

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Kling AI Best Practices](https://docs.klingai.com/best-practices)
- [API Error Reference](https://docs.klingai.com/errors)
- [Security Guidelines](https://docs.klingai.com/security)