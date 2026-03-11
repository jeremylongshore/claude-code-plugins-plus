---
name: vercel-debug-bundle
description: |
  Execute collect Vercel debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Vercel problems.
  Trigger with phrases like "vercel debug", "vercel support bundle",
  "collect vercel logs", "vercel diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Vercel Debug Bundle

## Prerequisites
- Vercel SDK installed
- Access to application logs
- Permission to collect environment info


See `${CLAUDE_SKILL_DIR}/references/implementation.md` for detailed implementation guide.

## Output
- `vercel-debug-YYYYMMDD-HHMMSS.tar.gz` archive containing:
  - `summary.txt` - Environment and SDK info
  - `logs.txt` - Recent redacted logs
  - `config-redacted.txt` - Configuration (secrets removed)

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Vercel Support](https://vercel.com/docs/support)
- [Vercel Status](https://www.vercel-status.com)
