---
name: speak-debug-bundle
description: |
  Collect Speak debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Speak problems.
  Trigger with phrases like "speak debug", "speak support bundle",
  "collect speak logs", "speak diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak Debug Bundle

## Overview
Collect all necessary diagnostic information for Speak support tickets.

## Prerequisites
- Speak SDK installed
- Access to application logs
- Permission to collect environment info

## Instructions
1. **Complete Script**
2. **Sensitive Data Handling**
3. **Submit to Support**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- `speak-debug-YYYYMMDD-HHMMSS.tar.gz` archive containing:
  - `summary.txt` - Environment and SDK info
  - `logs.txt` - Recent redacted logs
  - `sessions.txt` - Recent session activity
  - `config-redacted.txt` - Configuration (secrets removed)

## Resources
- [Speak Support Portal](https://support.speak.com)
- [Speak Status](https://status.speak.com)
- [Developer Community](https://community.speak.com)

## Next Steps
For rate limit issues, see `speak-rate-limits`.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with debugging |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply speak debug bundle to a standard project setup with default configuration options.

**Advanced scenario**: Customize speak debug bundle for production environments with multiple constraints and team-specific requirements.