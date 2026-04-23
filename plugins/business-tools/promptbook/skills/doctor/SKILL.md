---
name: doctor
description: |
  Diagnose Promptbook setup — check config, hooks, API key, and session tracking health.
  Use when Promptbook seems broken or the user wants to verify their setup.
  Trigger with "/doctor" or "check promptbook health".
version: 1.4.0
author: Promptbook <contact@promptbook.gg>
license: MIT
allowed-tools: Bash(node:*), Bash(curl:*), Bash(ls:*), Bash(stat:*), Bash(cat:*), Read
compatible-with: claude-code
tags: [analytics, telemetry, diagnostics, health-check]
---

# Promptbook Doctor

## Overview

Run diagnostics to verify Promptbook is set up correctly. Checks config, consent, API key validity, and recent session activity. Presents a clear pass/fail report.

## Prerequisites

- Promptbook must have been set up via `/setup` first
- Node.js installed (used for config parsing)
- Internet access (for API key verification)

## Instructions

Run these checks in order via Bash and report each result.

### 1. Config file exists

```bash
if [ -f "$HOME/.promptbook/config.json" ]; then
  echo "CONFIG_FOUND"
  # Check permissions — should be 600 for security
  stat -f "%Lp" "$HOME/.promptbook/config.json" 2>/dev/null || stat -c "%a" "$HOME/.promptbook/config.json" 2>/dev/null
  # Check required fields exist (without displaying values)
  node -e "const c=JSON.parse(require('fs').readFileSync('$HOME/.promptbook/config.json','utf8'));console.log('has_api_key:',!!c.api_key);console.log('has_api_url:',!!c.api_url);console.log('auto_summary:',c.auto_summary);console.log('telemetry_consent:',c.telemetry_consent===true)"
else
  echo "NO_CONFIG"
fi
```

If no config file found or `telemetry_consent` is false: tell the user to run `/setup` first.

### 2. API key is valid

Test the API key without displaying it:

```bash
API_KEY=$(node -e "console.log(JSON.parse(require('fs').readFileSync('$HOME/.promptbook/config.json','utf8')).api_key)")
curl -sL -o /dev/null -w "%{http_code}" -X POST "https://promptbook.gg/api/auth/verify-setup" \
  -H "Authorization: Bearer $API_KEY"
```

- 200 = valid and verified
- 401 = invalid key — suggest running `/setup` again
- Other = network issue — suggest checking connectivity

### 3. Last session activity

Check for recent session data files to verify hooks are firing:

```bash
ls -lt ~/.promptbook/sessions/ 2>/dev/null | head -5
```

If no session files found: hooks may not be firing. Suggest starting a new Claude Code session.

## Output

Present results as a clear diagnostic report:

```
Promptbook Doctor
─────────────────
✓ Config:    Found (~/.promptbook/config.json)
✓ Consent:   Granted during setup
✓ API Key:   Valid and verified
✓ Activity:  Last session 2 hours ago
```

Use `✓` for passing checks, `✗` for failures, `⚠` for warnings.

## Error Handling

- If config file is missing, report `✗ Config` and direct user to `/setup`
- If consent is false, report `✗ Consent` and direct user to `/setup`
- If API key returns 401, report `✗ API Key` and suggest re-running `/setup`
- If no session files exist, report `⚠ Activity` and suggest starting a new session
- Never display the API key in the report

## Examples

```
User: /doctor
Agent: Promptbook Doctor
       ─────────────────
       ✓ Config:    Found (~/.promptbook/config.json), permissions 600
       ✓ Consent:   Granted during setup
       ✓ API Key:   Valid and verified (HTTP 200)
       ✗ Activity:  No recent sessions found
       
       Everything looks good except no sessions have been tracked yet.
       Start a new Claude Code session to see your first build.
```

## Resources

- [Promptbook website](https://promptbook.gg)
- [Plugin repository](https://github.com/promptbookgg/claude-code-plugin)
