---
name: clay-prod-checklist
description: |
  Execute production readiness checklist for Clay integrations.
  Use when launching Clay-powered enrichment pipelines, preparing for go-live,
  or auditing production Clay configurations.
  Trigger with phrases like "clay production", "clay go-live", "clay launch checklist",
  "clay production readiness", "deploy clay pipeline".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, deployment]

---
# Clay Production Checklist

## Overview

Complete checklist for launching Clay enrichment pipelines in production. Covers table configuration, credit budgeting, webhook reliability, CRM sync validation, and monitoring setup.

## Prerequisites

- Clay table tested with sample data (100+ rows enriched successfully)
- CRM integration tested in staging
- Credit budget approved for monthly volume
- Team trained on Clay table management

## Instructions

### Phase 1: Table Configuration

- [ ] **Table schema finalized** -- all columns named, typed, and ordered
- [ ] **Enrichment columns configured** -- each column has correct provider and input mapping
- [ ] **Waterfall configured** -- providers ordered cheapest-first with "stop on first result"
- [ ] **Auto-run settings verified** -- table-level auto-update ON, column-level auto-run ON for needed columns
- [ ] **Conditional run rules set** -- enrichments only trigger when input data exists
- [ ] **Formula columns tested** -- ICP scoring and lead grading formulas validated
- [ ] **AI/Claygent columns reviewed** -- prompts produce consistent, quality output

### Phase 2: Data Quality Gates

- [ ] **Input validation in place** -- scripts validate data before webhook submission
- [ ] **Personal email filter** -- gmail.com, yahoo.com, etc. blocked from enrichment
- [ ] **Deduplication active** -- duplicate records detected before sending to Clay
- [ ] **Sample enrichment run completed** -- 500+ row test with >60% email find rate
- [ ] **Credit cost per row calculated** -- know your average credits per enriched lead

```typescript
// Pre-submission validation (run before pushing to Clay)
function validateForProduction(rows: any[]): { valid: any[]; rejected: any[] } {
  const personalDomains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com'];
  const seen = new Set<string>();
  const valid: any[] = [];
  const rejected: any[] = [];

  for (const row of rows) {
    const key = `${row.domain}:${row.first_name}:${row.last_name}`.toLowerCase();

    if (!row.domain?.includes('.'))
      rejected.push({ row, reason: 'invalid domain' });
    else if (personalDomains.some(d => row.domain.endsWith(d)))
      rejected.push({ row, reason: 'personal email domain' });
    else if (seen.has(key))
      rejected.push({ row, reason: 'duplicate' });
    else {
      seen.add(key);
      valid.push(row);
    }
  }

  console.log(`Validation: ${valid.length} valid, ${rejected.length} rejected (${(rejected.length / rows.length * 100).toFixed(1)}% filtered)`);
  return { valid, rejected };
}
```

### Phase 3: Credit & Cost Controls

- [ ] **Monthly credit budget set** -- know your plan's monthly credits
- [ ] **Table row limits configured** -- max rows set to prevent runaway enrichment
- [ ] **Provider API keys connected** -- own keys for high-volume providers (saves 70-80%)
- [ ] **Credit burn monitoring** -- alerts when daily usage exceeds threshold
- [ ] **Webhook submission counter** -- tracking against 50K lifetime limit

| Plan | Monthly Credits | Actions | HTTP API | Webhook Limit |
|------|----------------|---------|----------|---------------|
| Launch | 2,500 | 15,000 | No | 50K/webhook |
| Growth | 6,000 | 40,000 | Yes | 50K/webhook |
| Enterprise | Custom | Custom | Yes | 50K/webhook |

### Phase 4: Integration Reliability

- [ ] **Webhook endpoint health check** -- Clay can reach your callback URL
- [ ] **Retry logic implemented** -- 429 and 5xx responses handled with backoff
- [ ] **CRM sync tested** -- enriched records correctly map to CRM objects
- [ ] **HTTP API columns tested** -- outbound API calls return expected data
- [ ] **Error handling for empty enrichments** -- graceful handling when providers return no data

```bash
# Pre-flight connectivity checks
echo "=== Clay Production Pre-flight ==="

# 1. Webhook reachable
curl -s -o /dev/null -w "Webhook: HTTP %{http_code}\n" \
  -X POST "$CLAY_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"_preflight": true}'

# 2. Enterprise API (if applicable)
if [ -n "${CLAY_API_KEY:-}" ]; then
  curl -s -o /dev/null -w "Enterprise API: HTTP %{http_code}\n" \
    -X POST "https://api.clay.com/v1/people/enrich" \
    -H "Authorization: Bearer $CLAY_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com"}'
fi

# 3. Callback endpoint reachable
curl -s -o /dev/null -w "Callback endpoint: HTTP %{http_code}\n" \
  "https://your-app.com/api/health"
```

### Phase 5: Monitoring & Alerting

- [ ] **Credit consumption tracked** -- daily/weekly credit usage logged
- [ ] **Enrichment hit rate monitored** -- alert if email find rate drops below 40%
- [ ] **Webhook delivery failures alerted** -- notification on 4xx/5xx from webhooks
- [ ] **CRM sync errors tracked** -- alert on failed CRM pushes
- [ ] **Table row count monitored** -- alert when approaching plan limits

### Phase 6: Documentation & Runbooks

- [ ] **Table schema documented** -- column purposes, providers, and dependencies
- [ ] **Credit cost model documented** -- expected cost per lead at current volume
- [ ] **Webhook rotation procedure** -- steps to replace exhausted webhook (50K limit)
- [ ] **Provider failover plan** -- what to do when a provider is down
- [ ] **On-call escalation path** -- who to contact for Clay issues

## Error Handling

| Alert | Condition | Action |
|-------|-----------|--------|
| Credit balance low | < 500 credits remaining | Pause enrichments, add credits or connect own keys |
| Email find rate drop | < 40% for 2+ hours | Check input data quality, review provider status |
| Webhook 429s | > 5 per hour | Reduce submission rate, check plan limits |
| CRM sync failures | > 10 per batch | Check CRM field mapping, verify API key |

## Resources

- [Clay Plans & Billing](https://university.clay.com/docs/plans-and-billing)
- [Clay University -- Table Management](https://university.clay.com/docs/table-management-settings)

## Next Steps

For version upgrades, see `clay-upgrade-migration`.
