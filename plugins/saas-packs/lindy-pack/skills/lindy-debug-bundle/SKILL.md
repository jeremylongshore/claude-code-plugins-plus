---
name: lindy-debug-bundle
description: |
  Comprehensive debugging toolkit for Lindy AI agents.
  Use when investigating complex agent failures, collecting diagnostics,
  or preparing support tickets for Lindy support.
  Trigger with phrases like "lindy debug", "lindy diagnostics",
  "lindy support bundle", "investigate lindy issue".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, debugging]

---
# Lindy Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'Node.js not installed'`
!`python3 --version 2>/dev/null || echo 'Python not installed'`
!`curl --version 2>/dev/null | head -1 || echo 'curl not installed'`

## Overview
Systematic diagnostics for Lindy AI agent issues. Collects environment info,
tests API connectivity, reviews agent task history, and generates a support
bundle for Lindy's support team.

## Prerequisites
- Access to Lindy dashboard (https://app.lindy.ai)
- curl installed for API testing
- Agent ID and webhook URLs available

## Instructions

### Step 1: Collect Environment Info
```bash
# Local environment diagnostics
echo "=== Local Environment ==="
echo "Node: $(node --version 2>/dev/null || echo 'N/A')"
echo "Python: $(python3 --version 2>/dev/null || echo 'N/A')"
echo "OS: $(uname -srm)"
echo "Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo "LINDY_API_KEY set: $([ -n "$LINDY_API_KEY" ] && echo 'yes' || echo 'NO')"
echo "LINDY_WEBHOOK_SECRET set: $([ -n "$LINDY_WEBHOOK_SECRET" ] && echo 'yes' || echo 'NO')"
```

### Step 2: Test Webhook Connectivity
```bash
# Test webhook trigger endpoint
echo "=== Webhook Connectivity ==="
WEBHOOK_URL="${LINDY_WEBHOOK_URL:-https://public.lindy.ai/api/v1/webhooks/YOUR_ID}"

# Test without auth (expect 401)
echo "Without auth (expect 401):"
curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s\n" \
  -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Test with auth (expect 200)
echo "With auth (expect 200):"
curl -s -o /dev/null -w "HTTP %{http_code} in %{time_total}s\n" \
  -X POST "$WEBHOOK_URL" \
  -H "Authorization: Bearer $LINDY_WEBHOOK_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"test": true, "debug": "bundle-test"}'
```

### Step 3: Review Agent Task History
In the Lindy dashboard:
1. Navigate to the failing agent
2. Open the **Tasks** tab
3. Filter by **Failed** status
4. For each failed task:
   - Note the timestamp
   - Click to expand step-by-step execution
   - Identify the failing step (marked red)
   - Copy the error message and input/output data
5. Look for patterns: same step failing? same time of day? same input type?

### Step 4: Check Integration Health
```bash
# Test outbound connectivity to common Lindy integration targets
echo "=== Integration Targets ==="
for url in \
  "https://public.lindy.ai" \
  "https://slack.com/api/auth.test" \
  "https://www.googleapis.com/gmail/v1/users/me/profile" \
  "https://api.notion.com/v1/users/me"
do
  status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null)
  echo "$url -> HTTP $status"
done
```

### Step 5: Diagnose Specific Failure Types

**Trigger not firing**:
- Verify agent status: active (not paused)
- Check trigger filter conditions
- For webhooks: test URL with curl
- For email: re-authorize Gmail/Outlook
- For schedule: verify timezone settings

**Action failing**:
- Check integration authorization (re-auth if token expired)
- Verify field references: `{{step_name.field}}` syntax correct
- Test the target service independently
- Check if action is a Premium Action (requires Pro plan)

**Agent step looping**:
- Review exit conditions — are they achievable?
- Check credit consumption (rapid drain = looping)
- Reduce available skills to 2-4 focused ones
- Add a fallback exit condition

**High credit consumption**:
- Review model selection: Gemini Flash (cheap) vs GPT-4 (expensive)
- Check for unnecessary agent steps (use deterministic actions instead)
- Review loop configurations for unbounded max cycles

### Step 6: Generate Support Bundle
Compile the following for a support ticket to support@lindy.ai:
```markdown
## Lindy Support Bundle

**Account**: [your email]
**Agent Name**: [agent name]
**Agent URL**: https://app.lindy.ai/agents/[agent-id]
**Issue Start**: [date/time UTC]
**Frequency**: [every time / intermittent / once]

### Environment
- Browser: [Chrome/Firefox/Safari version]
- Plan: [Free/Pro/Business/Enterprise]
- Credit Balance: [remaining credits]

### Reproduction Steps
1. [step 1]
2. [step 2]

### Failed Task IDs
- [task-id-1] at [timestamp]
- [task-id-2] at [timestamp]

### Error Messages
[Copy exact error text from task detail view]

### What I Tried
- [attempt 1]
- [attempt 2]
```

## Diagnostic Decision Tree

```
Agent not working?
├── No task created → Check trigger configuration
│   ├── Webhook? → Test with curl (Step 2)
│   ├── Email? → Re-authorize + check filters
│   └── Schedule? → Check timezone + credit balance
├── Task created but failed → Check task detail view
│   ├── Trigger step failed → Auth/connectivity issue
│   ├── Action step failed → Integration auth expired
│   ├── Condition step failed → Ambiguous condition prompt
│   └── Agent step looping → Exit conditions unreachable
└── Task completed but wrong result → Prompt/config issue
    ├── Wrong output → Refine agent prompt
    ├── Missing data → Check field references
    └── Partial execution → Review condition branches
```

## Error Handling

| Symptom | Likely Cause | Resolution |
|---------|-------------|------------|
| All agents failing simultaneously | Lindy platform outage | Check status.lindy.ai |
| Single agent failing | Agent-specific config issue | Review task detail view |
| Intermittent failures | Rate limits or credit exhaustion | Check usage dashboard |
| Slow execution | Model too large or too many steps | Switch to Gemini Flash, consolidate steps |

## Resources
- [Lindy Community](https://community.lindy.ai)
- [Lindy Documentation](https://docs.lindy.ai)
- [Lindy Status](https://status.lindy.ai)

## Next Steps
Proceed to `lindy-rate-limits` for credit and rate management.
