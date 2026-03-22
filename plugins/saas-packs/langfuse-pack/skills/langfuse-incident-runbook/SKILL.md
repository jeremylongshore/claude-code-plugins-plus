---
name: langfuse-incident-runbook
description: |
  Troubleshoot and respond to Langfuse-related incidents and outages.
  Use when experiencing Langfuse outages, debugging production issues,
  or responding to LLM observability incidents.
  Trigger with phrases like "langfuse incident", "langfuse outage",
  "langfuse down", "langfuse production issue", "langfuse troubleshoot".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langfuse, observability, llm, debugging]

---
# Langfuse Incident Runbook

## Overview
Step-by-step procedures for Langfuse-related incidents, from initial triage (2 min) through resolution and post-incident review. Your application should work without Langfuse -- these procedures focus on restoring observability.

## Severity Classification

| Severity | Description | Response Time | Example |
|----------|-------------|---------------|---------|
| P1 | Application impacted by tracing | 15 min | SDK throwing unhandled errors, blocking requests |
| P2 | Traces not appearing, no app impact | 1 hour | Missing observability data |
| P3 | Degraded performance from tracing | 4 hours | High latency from flush backlog |
| P4 | Minor issues | 24 hours | Occasional missing traces |

## Instructions

### Step 1: Initial Assessment (2 Minutes)

```bash
set -euo pipefail
echo "=== Langfuse Incident Triage ==="
echo "Time: $(date -u)"

# 1. Check Langfuse cloud status
echo -n "Status page: "
curl -s -o /dev/null -w "%{http_code}" https://status.langfuse.com || echo "UNREACHABLE"
echo ""

# 2. Test API connectivity
HOST="${LANGFUSE_BASE_URL:-${LANGFUSE_HOST:-https://cloud.langfuse.com}}"
echo -n "API health: "
curl -s -o /dev/null -w "%{http_code} (%{time_total}s)" "$HOST/api/public/health" || echo "FAILED"
echo ""

# 3. Test auth
if [ -n "${LANGFUSE_PUBLIC_KEY:-}" ] && [ -n "${LANGFUSE_SECRET_KEY:-}" ]; then
  AUTH=$(echo -n "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" | base64)
  echo -n "Auth test: "
  curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Basic $AUTH" "$HOST/api/public/traces?limit=1" || echo "FAILED"
  echo ""
fi

# 4. Check app error logs
echo ""
echo "--- Recent errors ---"
grep -i "langfuse\|trace.*error\|flush.*fail" /var/log/app/*.log 2>/dev/null | tail -10 || echo "No log files found"
```

### Step 2: Determine Incident Type and Response

| Symptom | Likely Cause | Immediate Action |
|---------|--------------|-----------------|
| No traces appearing | SDK not flushing | Check shutdown handlers; set `flushAt: 1` temporarily |
| `401 Unauthorized` | Key rotation or mismatch | Verify keys match the correct project |
| `429 Too Many Requests` | Rate limited | Increase batch size, reduce flush frequency |
| SDK throwing errors | Unhandled exception | Wrap in try/catch; check SDK version |
| High request latency | Sync flush in hot path | Switch to async; increase `requestTimeout` |
| Complete Langfuse outage | Service-side issue | Enable fallback mode |

### Step 3: Fallback Mode (P1 -- App Impacted)

If Langfuse is causing application issues, disable tracing immediately:

```typescript
// Emergency disable via environment variable
// Set LANGFUSE_ENABLED=false in your deployment

// In your tracing initialization:
if (process.env.LANGFUSE_ENABLED === "false") {
  console.warn("Langfuse tracing DISABLED (emergency fallback)");
  // Don't initialize SDK -- all observe/startActiveObservation calls
  // will still work but produce no-op spans
}
```

For v3, use the `enabled` flag:
```typescript
const langfuse = new Langfuse({
  enabled: process.env.LANGFUSE_ENABLED !== "false",
});
```

### Step 4: Common Resolution Procedures

**Procedure A: Missing Traces**
```typescript
// 1. Verify SDK is initialized
console.log("Langfuse configured:", !!process.env.LANGFUSE_PUBLIC_KEY);

// 2. Check flush is happening
// v4+: Verify NodeSDK is started and shutdown is registered
// v3: Verify flushAsync() or shutdownAsync() is called

// 3. Temporarily set aggressive flush for debugging
const processor = new LangfuseSpanProcessor({
  exportIntervalMillis: 1000,
  maxExportBatchSize: 1,
});
```

**Procedure B: Rate Limit (429) Recovery**
```typescript
// Increase batching to reduce API calls
const processor = new LangfuseSpanProcessor({
  exportIntervalMillis: 30000, // 30s flush
  maxExportBatchSize: 200,     // Large batches
});

// Or temporarily enable sampling
const EMERGENCY_SAMPLE_RATE = 0.1; // Only trace 10%
```

**Procedure C: Self-Hosted Instance Down**
```bash
set -euo pipefail
# Check container status
docker ps -a | grep langfuse

# Check logs
docker logs langfuse-langfuse-1 --tail 50

# Check database
docker exec langfuse-postgres-1 pg_isready -U langfuse

# Restart if needed
docker compose restart langfuse
```

### Step 5: Post-Incident Verification

```bash
set -euo pipefail
# Verify traces are flowing again
echo "=== Post-Incident Check ==="

HOST="${LANGFUSE_BASE_URL:-https://cloud.langfuse.com}"
AUTH=$(echo -n "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" | base64)

# Check recent trace count
TRACE_COUNT=$(curl -s \
  -H "Authorization: Basic $AUTH" \
  "$HOST/api/public/traces?limit=5" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))" 2>/dev/null || echo "ERROR")

echo "Recent traces: $TRACE_COUNT"

if [ "$TRACE_COUNT" = "0" ] || [ "$TRACE_COUNT" = "ERROR" ]; then
  echo "WARNING: Traces may not be flowing yet"
else
  echo "OK: Traces are appearing"
fi
```

### Step 6: Post-Incident Review (P1/P2)

Document for post-mortem:
1. **Timeline**: When detected, when resolved, total duration
2. **Impact**: Traces lost, application impact, user impact
3. **Root cause**: Why did the incident occur?
4. **Resolution**: What fixed it?
5. **Prevention**: What changes prevent recurrence?
6. **Action items**: Improvements to implement

## Escalation Path

| Level | Who | When |
|-------|-----|------|
| L1 | On-call engineer | All incidents -- run triage |
| L2 | Platform team lead | P1/P2 unresolved after 30 min |
| L3 | Langfuse support | Confirmed service-side issue |

**Langfuse support channels:**
- [Status Page](https://status.langfuse.com) -- check first
- [Discord](https://langfuse.com/discord) -- community support
- [GitHub Issues](https://github.com/langfuse/langfuse/issues) -- bug reports
- Email support (enterprise customers)

## Error Handling

| Issue | Immediate Fix | Permanent Fix |
|-------|--------------|---------------|
| SDK crashes app | Set `LANGFUSE_ENABLED=false` | Wrap all tracing in try/catch |
| Lost traces | Increase batch size | Add shutdown handlers |
| High latency | Disable sync flush | Use async-only patterns |
| Auth failures | Rotate and redeploy keys | Add key validation at startup |

## Resources
- [Langfuse Status](https://status.langfuse.com)
- [GitHub Issues](https://github.com/langfuse/langfuse/issues)
- [Discord Community](https://langfuse.com/discord)
- [Self-Hosting Troubleshooting](https://langfuse.com/self-hosting/configuration)
