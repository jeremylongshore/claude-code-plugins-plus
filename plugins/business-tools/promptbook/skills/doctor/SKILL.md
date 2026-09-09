---
name: doctor
description: Diagnose Promptbook setup — check config, hooks, API key, and session tracking health
version: 1.4.0
author: Promptbook
license: MIT
allowed-tools: Bash
---

# Promptbook Doctor

Run diagnostics to check if Promptbook is set up correctly. Execute each check via Bash and report the results.

## Checks

Run these checks in order and report each result:

### 1. Config file exists

```bash
if [ -f "$HOME/.promptbook/config.json" ]; then
  echo "CONFIG_FOUND"
  # Check permissions (should be 600)
  stat -f "%Lp" "$HOME/.promptbook/config.json" 2>/dev/null || stat -c "%a" "$HOME/.promptbook/config.json" 2>/dev/null
  # Check required fields exist (without displaying values)
  node -e "const c=JSON.parse(require('fs').readFileSync('$HOME/.promptbook/config.json','utf8'));console.log('has_api_key:',!!c.api_key);console.log('has_api_url:',!!c.api_url);console.log('auto_summary:',c.auto_summary);console.log('telemetry_consent:',c.telemetry_consent===true)"
else
  echo "NO_CONFIG"
fi
```

If no config file found or `telemetry_consent` is false: tell the user to run `/setup` first.

### 2. API key is valid
Use the config file to test the API key without displaying it:

```bash
API_KEY=$(node -e "console.log(JSON.parse(require('fs').readFileSync('$HOME/.promptbook/config.json','utf8')).api_key)")
curl -sL -o /dev/null -w "%{http_code}" -X POST "https://promptbook.gg/api/auth/verify-setup" \
  -H "Authorization: Bearer $API_KEY"
```

- 200 = valid and verified
- 401 = invalid key — suggest running `/setup` again
- Other = network issue — suggest checking connectivity

### 3. Last session activity
Check for recent session data files to see if hooks are actually firing:

```bash
ls -lt ~/.promptbook/sessions/ 2>/dev/null | head -5
```

If no session files found: hooks may not be firing. Suggest starting a new Claude Code session.

## Report Format

Present results as a clear diagnostic:

```
Promptbook Doctor
─────────────────
✓ Config:    Found (~/.promptbook/config.json)
✓ Consent:   Granted during setup
✓ API Key:   Valid and verified
✓ Activity:  Last session 2 hours ago
```

Use ✓ for passing checks, ✗ for failures, ⚠ for warnings.

## Important
- Run all commands via Bash — the user just reads the report.
- Never display the API key.
- If everything passes, tell the user their setup is healthy.
- If checks fail, give specific actionable steps to fix each issue.
