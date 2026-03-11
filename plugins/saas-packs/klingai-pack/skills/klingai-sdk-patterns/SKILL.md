---
name: klingai-sdk-patterns
description: |
  Implement common SDK patterns for Kling AI integration. Use when building production applications
  with Kling AI. Trigger with phrases like 'klingai sdk', 'kling ai client', 'klingai patterns',
  'kling ai best practices'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Klingai Sdk Patterns

## Overview

This skill covers proven SDK patterns including client initialization, error handling, retry logic, async job management, and configuration management for robust Kling AI integrations.

## Prerequisites

- Kling AI API key configured
- Python 3.8+ or Node.js 18+
- Understanding of async programming concepts

## Instructions

Follow these steps to implement SDK patterns:

1. **Create Client Wrapper**: Build a reusable client class
2. **Implement Error Handling**: Add robust error handling
3. **Add Retry Logic**: Handle transient failures
4. **Manage Async Jobs**: Track generation jobs properly
5. **Configure Timeouts**: Set appropriate timeout values

## Output

Successful execution produces:
- Robust, production-ready client code
- Proper error handling and retry logic
- Async job management patterns

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Kling AI API Reference](https://docs.klingai.com/api)
- [Error Codes](https://docs.klingai.com/errors)
- [Rate Limits](https://docs.klingai.com/rate-limits)