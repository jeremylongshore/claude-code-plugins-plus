---
name: klingai-debug-bundle
description: |
  Execute set up comprehensive logging and debugging for Kling AI. Use when investigating issues or
  monitoring requests. Trigger with phrases like 'klingai debug', 'kling ai logging',
  'trace klingai', 'monitor klingai requests'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Klingai Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview

This skill shows how to implement request/response logging, timing metrics, and debugging utilities for Kling AI integrations to quickly identify and resolve issues.

## Prerequisites

- Kling AI integration
- Python 3.8+ or Node.js 18+
- Logging infrastructure (optional but recommended)

## Instructions

Follow these steps to set up debugging:

1. **Configure Logging**: Set up structured logging
2. **Add Request Tracing**: Track all API requests
3. **Implement Timing**: Measure performance metrics
4. **Create Debug Utilities**: Build diagnostic tools
5. **Set Up Alerts**: Configure error notifications

## Output

Successful execution produces:
- Structured logging output
- Request traces with timing
- Performance metrics dashboard
- Debug reports for troubleshooting

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Python Logging](https://docs.python.org/3/library/logging.html)
- [Structured Logging Best Practices](https://www.structlog.org/)
- [OpenTelemetry](https://opentelemetry.io/)