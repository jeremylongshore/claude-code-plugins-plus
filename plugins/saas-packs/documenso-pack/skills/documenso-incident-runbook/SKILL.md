---
name: documenso-incident-runbook
description: |
  Manage incident response for Documenso integration issues.
  Use when diagnosing production incidents, handling outages,
  or responding to Documenso service disruptions.
  Trigger with phrases like "documenso incident", "documenso outage",
  "documenso down", "documenso troubleshooting".
allowed-tools: Read, Bash(curl:*), Bash(kubectl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, incident-response]

---
# Documenso Incident Runbook

## Overview

Step-by-step procedures for responding to Documenso integration incidents. Covers cloud outages, self-hosted issues, and integration failures.

## Prerequisites

- Access to monitoring dashboards
- Documenso dashboard access
- Application log access
- On-call escalation contacts defined

## Severity Levels

| Level | Description | Examples | Response Time |
|-------|-------------|----------|---------------|
| P1 | Complete signing outage | All API calls failing, no documents can be sent | < 15 min |
| P2 | Degraded functionality | Slow responses, intermittent errors, webhooks delayed | < 1 hour |
| P3 | Minor issue, workaround available | Single document stuck, UI glitch | < 4 hours |
| P4 | Non-urgent | Feature request, documentation gap | Next business day |

## Quick Diagnostic Commands

```bash
#!/bin/bash
set -euo pipefail
echo "=== Documenso Incident Diagnostic ==="

# 1. Check Documenso cloud status
echo "--- Cloud Status ---"
curl -s https://status.documenso.com/api/v2/status.json 2>/dev/null | jq '.status' || echo "Status page unreachable"

# 2. Check our API connectivity
echo "--- API Connectivity ---"
BASE="${DOCUMENSO_BASE_URL:-https://app.documenso.com/api/v1}"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
  "$BASE/documents?page=1&perPage=1" 2>/dev/null || echo "000")
echo "API Status: $HTTP_CODE"

# 3. Check latency (5 samples)
echo "--- Latency Check ---"
for i in $(seq 1 5); do
  LATENCY=$(curl -s -o /dev/null -w "%{time_total}" \
    -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
    "$BASE/documents?page=1&perPage=1" 2>/dev/null || echo "timeout")
  echo "  Request $i: ${LATENCY}s"
done

# 4. Self-hosted: check container status
echo "--- Self-Hosted Container (if applicable) ---"
docker ps --filter "name=documenso" --format "{{.Names}}: {{.Status}}" 2>/dev/null || echo "Docker not available or Documenso not self-hosted"
```

## Incident Response Procedures

### Scenario 1: Documenso Cloud Outage (5xx Errors)

**Symptoms:** High error rate, 500/502/503 from Documenso API.

**Actions:**
1. Check status page: https://status.documenso.com
2. If Documenso confirms outage:
   - Enable degraded mode in your app
   - Queue signing requests for later
   - Show user-facing message: "Document signing temporarily unavailable"
   - Monitor status page for resolution
3. If Documenso shows operational but you see errors:
   - Check your API key validity (could be rotated/revoked)
   - Check if specific endpoints fail (documents vs templates)
   - Review recent deployments for breaking changes
   - Contact Documenso support with diagnostic output

### Scenario 2: Self-Hosted Database Issues

**Symptoms:** Container running but API returns errors, migrations failing.

```bash
# Check PostgreSQL health
docker exec documenso-db pg_isready -U documenso

# Check Documenso container logs
docker logs documenso --tail 100 | grep -i "error\|fatal\|prisma"

# Check if migrations ran
docker logs documenso --tail 50 | grep "prisma migrate"

# Check database connectivity from Documenso container
docker exec documenso curl -s http://localhost:3000/api/health || echo "Internal health check failed"
```

### Scenario 3: Webhook Delivery Failures

**Symptoms:** Webhooks not arriving, document events not triggering workflows.

```text
Checklist:
1. Verify webhook is enabled in Team Settings > Webhooks
2. Check your endpoint is returning 200 within 10 seconds
3. Verify HTTPS is working (Documenso won't send to HTTP)
4. Check X-Documenso-Secret matches your stored secret
5. Review your webhook handler logs for exceptions
6. If using ngrok: confirm tunnel is active
```

### Scenario 4: Signing Certificate Expired (Self-Hosted)

**Symptoms:** Documents can be sent but signatures are invalid or rejected by verification tools.

```bash
# Check certificate expiry
openssl pkcs12 -in /path/to/signing-cert.p12 -nokeys -passin pass:$CERT_PASSPHRASE | openssl x509 -noout -dates

# If expired:
# 1. Obtain new certificate from your CA
# 2. Mount new certificate into container
# 3. Restart container: docker compose restart documenso
# 4. Verify: create and sign a test document
```

## Emergency Circuit Breaker

```typescript
// src/emergency/circuit-breaker.ts
class DocumensoCircuitBreaker {
  private isOpen = false;
  private openedAt = 0;
  private readonly cooldownMs = 60000; // 1 minute

  open(reason: string) {
    this.isOpen = true;
    this.openedAt = Date.now();
    console.error(`CIRCUIT BREAKER OPEN: ${reason}`);
    // Alert team via Slack/PagerDuty
  }

  close() {
    this.isOpen = false;
    console.log("Circuit breaker closed — Documenso operations resumed");
  }

  async execute<T>(fn: () => Promise<T>, fallback?: () => T): Promise<T> {
    if (this.isOpen) {
      // Auto-close after cooldown for half-open test
      if (Date.now() - this.openedAt > this.cooldownMs) {
        try {
          const result = await fn();
          this.close();
          return result;
        } catch {
          this.openedAt = Date.now(); // Reset cooldown
          if (fallback) return fallback();
          throw new Error("Documenso unavailable — circuit breaker open");
        }
      }
      if (fallback) return fallback();
      throw new Error("Documenso unavailable — circuit breaker open");
    }
    return fn();
  }
}
```

## Post-Incident Checklist

- [ ] Incident timeline documented (when detected, diagnosed, resolved)
- [ ] Root cause identified
- [ ] User impact quantified (how many documents affected)
- [ ] Fix verified in production
- [ ] Monitoring gaps identified and addressed
- [ ] Preventive measures implemented
- [ ] Post-mortem completed (for P1/P2)

## Communication Template

```text
INCIDENT: Documenso Integration Issue
Severity: P[X]
Status: Investigating | Identified | Mitigating | Resolved
Impact: [Number of users/documents affected]
Start: [ISO timestamp]

Summary: [Brief description]

Timeline:
- [HH:MM] Issue detected via [monitoring/user report]
- [HH:MM] Root cause identified: [cause]
- [HH:MM] Fix deployed / workaround applied
- [HH:MM] Resolved, monitoring for recurrence

Action Items:
- [ ] [Preventive measure 1]
- [ ] [Preventive measure 2]
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Persistent 5xx | Documenso outage | Enable circuit breaker, queue requests |
| Self-hosted crash loop | Bad migration or config | Check `docker logs`, rollback image |
| Certificate invalid | Expired or wrong cert | Replace `.p12` file, restart container |
| All webhooks failing | Endpoint down | Check HTTPS endpoint, verify health |

## Resources

- [Documenso Status](https://status.documenso.com)
- [Documenso Discord](https://documenso.com/discord)
- [GitHub Issues](https://github.com/documenso/documenso/issues)
- [Self-Hosting Tips](https://docs.documenso.com/docs/self-hosting/getting-started/tips)

## Next Steps

For data handling procedures, see `documenso-data-handling`.
