---
name: lindy-incident-runbook
description: |
  Incident response procedures for Lindy AI agent failures and outages.
  Use when responding to incidents, troubleshooting agent outages,
  or creating on-call procedures for Lindy-powered systems.
  Trigger with phrases like "lindy incident", "lindy outage",
  "lindy on-call", "lindy runbook", "lindy down".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, incident-response]

---
# Lindy Incident Runbook

## Overview
Incident response procedures for Lindy AI agent failures. Covers platform outages,
individual agent failures, integration breakdowns, credit exhaustion, and webhook
endpoint failures.

## Incident Severity Levels

| Severity | Description | Response Time | Examples |
|----------|-------------|---------------|----------|
| SEV1 | All agents failing, customer impact | 15 minutes | Lindy platform outage, all webhooks failing |
| SEV2 | Critical agent down | 30 minutes | Support bot offline, phone agent unreachable |
| SEV3 | Degraded performance | 2 hours | High latency, intermittent failures |
| SEV4 | Minor issue | 24 hours | Non-critical agent misconfigured |

## Quick Diagnostics (First 5 Minutes)

### Step 1: Check Lindy Platform Status
```bash
# Is Lindy up?
curl -s -o /dev/null -w "Lindy API: HTTP %{http_code}\n" \
  "https://public.lindy.ai" --max-time 5

# Check status page
echo "Status page: https://status.lindy.ai"
```

### Step 2: Check Your Integration
```bash
# Is your webhook receiver up?
curl -s -o /dev/null -w "Our endpoint: HTTP %{http_code}\n" \
  "https://api.yourapp.com/health" --max-time 5

# Is the webhook auth working?
curl -s -o /dev/null -w "Webhook auth: HTTP %{http_code}\n" \
  -X POST "https://api.yourapp.com/lindy/callback" \
  -H "Authorization: Bearer $LINDY_WEBHOOK_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"test": true}' --max-time 5
```

### Step 3: Check Credit Balance
Log in at https://app.lindy.ai > Settings > Billing
- Credits at 0? Agents stop processing
- Credits low? Non-essential agents may be paused

## Incident Playbooks

### Incident: Lindy Platform Outage (SEV1)
**Symptoms**: All agents failing, status.lindy.ai shows incident
**Impact**: All Lindy-dependent workflows halted

**Runbook**:
1. Confirm outage at https://status.lindy.ai
2. Notify team: "Lindy platform outage confirmed. All agents affected."
3. Activate fallback procedures:
   - Route support emails to human inbox
   - Disable webhook triggers from your app
   - Queue events for replay when Lindy recovers
4. Monitor status page for recovery
5. When recovered: re-enable triggers, replay queued events, verify agent health

**Fallback code**:
```typescript
async function triggerLindyWithFallback(payload: any) {
  try {
    const response = await fetch(WEBHOOK_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${SECRET}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(10000), // 10s timeout
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return { routed: 'lindy' };
  } catch (error) {
    console.error('Lindy unreachable, activating fallback:', error);
    await queueForReplay(payload); // Store for later
    await notifyTeam(`Lindy trigger failed: ${error}`);
    return { routed: 'fallback' };
  }
}
```

### Incident: Individual Agent Failure (SEV2)
**Symptoms**: Specific agent tasks showing "Failed" status
**Impact**: One workflow affected, others may be fine

**Runbook**:
1. Open agent > Tasks tab > Filter by "Failed"
2. Click latest failed task — identify the failing step
3. Diagnose based on failing step type:
   - **Trigger step**: Auth expired? Filter too restrictive?
   - **Action step**: Integration token expired? Target API down?
   - **Condition step**: Ambiguous condition prompt?
   - **Agent step**: Looping? Exit conditions unreachable?
4. Fix the root cause:
   - Re-authorize expired integrations
   - Fix action configuration
   - Simplify condition prompts
   - Add fallback exit conditions
5. Test with a manual trigger
6. Monitor next 5 tasks for success

### Incident: Integration Auth Expired (SEV2-3)
**Symptoms**: Actions failing with "Not authorized" or "Token expired"
**Impact**: All tasks using that integration fail

**Runbook**:
1. Identify which integration is failing (Gmail, Slack, Sheets, etc.)
2. In Lindy dashboard: Settings > Integrations
3. Find the expired connection (may show warning icon)
4. Click **Re-authorize** and complete OAuth flow
5. Re-test the agent with a manual trigger
6. Set calendar reminder for 90-day re-authorization check

### Incident: Credit Exhaustion (SEV2-3)
**Symptoms**: Agents stop running, no new tasks created
**Impact**: All agents paused until credits refill

**Runbook**:
1. Confirm at Settings > Billing: credits at 0
2. Immediate: Upgrade plan or purchase additional credits
3. Investigate: Which agent consumed the most credits?
4. Root cause: trigger storm? looping agent step? large model overuse?
5. Fix: Add trigger filters, set exit conditions, downgrade model
6. Prevent: Set budget alerts at 50%, 80%, 95% thresholds

### Incident: Webhook Endpoint Failure (SEV2-3)
**Symptoms**: Lindy agent runs but your callback never receives data
**Impact**: Agent completes but results are lost

**Runbook**:
1. Check your endpoint health: `curl -s https://api.yourapp.com/health`
2. Check server logs for incoming requests from Lindy
3. Verify the HTTP Request action URL matches your production endpoint
4. Test endpoint independently: send a POST with curl
5. If endpoint was down: replay failed tasks (re-trigger the agent)
6. If URL mismatch: update URL in Lindy agent HTTP Request action

## Escalation Matrix

| Level | Contact | When |
|-------|---------|------|
| L1 | On-call engineer | Initial response, diagnostics |
| L2 | Engineering lead | After 30 min SEV1, 1 hour SEV2 |
| L3 | VP Engineering | After 1 hour SEV1 |
| Lindy Support | support@lindy.ai | Confirmed Lindy platform issue |

## Post-Incident Template
```markdown
## Incident Report

**Date**: YYYY-MM-DD
**Severity**: SEV[1-4]
**Duration**: [start time] to [end time] ([total minutes])
**Impact**: [what was affected, customer impact]

### Timeline
- HH:MM — Issue detected via [monitoring/user report]
- HH:MM — On-call paged, diagnostics started
- HH:MM — Root cause identified: [cause]
- HH:MM — Fix applied: [what was done]
- HH:MM — Service restored, monitoring confirmed

### Root Cause
[Technical description of what failed and why]

### Resolution
[What was done to fix it]

### Prevention
- [ ] [Action item 1]
- [ ] [Action item 2]
- [ ] [Action item 3]
```

## Error Handling

| Incident Type | Detection | Automated Response |
|--------------|-----------|-------------------|
| Platform outage | Health check fails | Queue events, notify team |
| Agent failure | Task Completed trigger | Slack alert to #ops |
| Auth expiry | Action step fails | Alert + re-auth link |
| Credit exhaustion | Billing check | Pause non-critical agents |
| Endpoint down | Health check | Redirect to fallback |

## Resources
- [Lindy Status](https://status.lindy.ai)
- [Lindy Support](mailto:support@lindy.ai)
- [Lindy Community](https://community.lindy.ai)

## Next Steps
Proceed to `lindy-data-handling` for data security and compliance.
