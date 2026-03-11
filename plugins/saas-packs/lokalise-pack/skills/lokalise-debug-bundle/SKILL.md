---
name: lokalise-debug-bundle
description: |
  Collect Lokalise debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Lokalise problems.
  Trigger with phrases like "lokalise debug", "lokalise support bundle",
  "collect lokalise logs", "lokalise diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Bash(lokalise2:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Debug Bundle

## Overview
Collect all necessary diagnostic information for Lokalise support tickets.

## Prerequisites
- Lokalise SDK/CLI installed
- Access to application logs
- Permission to collect environment info

## Instructions

1. For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- `lokalise-debug-YYYYMMDD-HHMMSS.tar.gz` archive containing:
  - `summary.txt` - Environment, SDK, and network info
  - `projects.json` - Project listing (if token available)
  - `logs-redacted.txt` - Application logs with secrets removed
  - `config-redacted.txt` - Configuration with secrets removed

## Error Handling
| Item | Purpose | Included |
|------|---------|----------|
| Environment versions | Compatibility check | Yes |
| SDK version | Version-specific bugs | Yes |
| Network tests | Connectivity issues | Yes |
| Rate limit status | Throttling issues | Yes |
| Error logs (redacted) | Root cause analysis | Yes |
| Config (redacted) | Configuration issues | Yes |

## Examples
**ALWAYS REDACT:**
- API tokens
- Webhook secrets
- OAuth credentials
- Email addresses
- User IDs (if PII)
**Safe to Include:**
- Error messages
- Stack traces (redacted)
- SDK/runtime versions
- Project IDs (non-sensitive)
- HTTP status codes
### One-Liner Quick Check
```bash
set -euo pipefail
# Quick API test
curl -s -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" \
  -H "X-Api-Token: $LOKALISE_API_TOKEN" \
  "https://api.lokalise.com/api2/projects?limit=1" | jq '.projects[0].name // .error'
```

## Resources
- [Lokalise Support](mailto:support@lokalise.com)
- [Lokalise Status](https://status.lokalise.com)
- [Community Forum](https://community.lokalise.com)

## Next Steps
For rate limit issues, see `lokalise-rate-limits`.