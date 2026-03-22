---
name: clay-advanced-troubleshooting
description: |
  Deep-debug complex Clay enrichment failures, provider degradation, and data flow issues.
  Use when standard troubleshooting fails, investigating intermittent enrichment failures,
  or preparing detailed evidence for Clay support escalation.
  Trigger with phrases like "clay hard bug", "clay mystery error",
  "clay impossible to debug", "difficult clay issue", "clay deep debug".
allowed-tools: Read, Grep, Bash(curl:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, debugging, scaling]

---
# Clay Advanced Troubleshooting

## Overview

Deep debugging techniques for complex Clay issues that resist standard troubleshooting. Covers provider-level isolation, waterfall diagnosis, HTTP API column debugging, Claygent failure analysis, and Clay support escalation with proper evidence.

## Prerequisites

- Access to Clay table with the failing enrichments
- curl and jq for API testing
- Understanding of Clay's enrichment architecture (providers, waterfall, columns)
- Browser developer tools for network inspection

## Instructions

### Step 1: Isolate the Failure Layer

```bash
#!/bin/bash
# clay-layer-test.sh — test each integration layer independently
set -euo pipefail

echo "=== Layer Isolation Test ==="

# Layer 1: Webhook delivery
echo "Layer 1: Webhook"
WEBHOOK_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "$CLAY_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"_debug": true, "domain": "google.com"}')
echo "  Webhook: $WEBHOOK_CODE"

# Layer 2: Enterprise API (if applicable)
if [ -n "${CLAY_API_KEY:-}" ]; then
  echo "Layer 2: Enterprise API"
  API_RESULT=$(curl -s -X POST "https://api.clay.com/v1/companies/enrich" \
    -H "Authorization: Bearer $CLAY_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"domain": "google.com"}')
  echo "  API response keys: $(echo "$API_RESULT" | jq 'keys')"
fi

# Layer 3: HTTP API callback endpoint
echo "Layer 3: Callback endpoint"
CALLBACK_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST "${CLAY_CALLBACK_URL:-http://localhost:3000/api/clay/enriched}" \
  -H "Content-Type: application/json" \
  -d '{"_debug_test": true}')
echo "  Callback: $CALLBACK_CODE"

echo ""
echo "First failing layer = root cause location"
```

### Step 2: Diagnose Enrichment Column Failures

In the Clay UI, click on red/error cells to see detailed error messages:

```yaml
# Common enrichment column error patterns and root causes:
errors:
  "No data found":
    meaning: "Provider has no data for this input"
    check:
      - Is the input domain valid? (not personal email domain)
      - Is the input name spelled correctly?
      - Is the provider connected? (Settings > Connections)
    fix: "Add more waterfall providers for broader coverage"

  "Rate limit exceeded":
    meaning: "Provider API rate limit hit"
    check:
      - How many rows are processing simultaneously?
      - Is the provider's rate limit known? (see provider docs)
    fix: "Reduce table row count, add delay between batches"

  "Invalid API key":
    meaning: "Provider connection lost or key expired"
    check:
      - Go to Settings > Connections
      - Click on the failing provider
      - Test the connection
    fix: "Reconnect with a valid API key"

  "Timeout":
    meaning: "Provider took too long to respond"
    check:
      - Is the provider's status page showing issues?
      - Is the input data unusually complex?
    fix: "Retry the column on failed rows (click cell > retry)"

  "Column dependency not met":
    meaning: "A column this enrichment depends on hasn't completed yet"
    check:
      - Check column order (left to right execution)
      - Is the prerequisite column populated?
    fix: "Reorder columns so dependencies run first"
```

### Step 3: Debug HTTP API Column Issues

```typescript
// debug/http-api-column.ts — replicate Clay's HTTP API column call locally
async function debugHTTPAPIColumn(
  url: string,
  method: string,
  headers: Record<string, string>,
  body: Record<string, string>,
  sampleRow: Record<string, string>,
): Promise<void> {
  // Replace {{column_name}} placeholders with sample data
  let resolvedUrl = url;
  let resolvedBody = JSON.stringify(body);

  for (const [key, value] of Object.entries(sampleRow)) {
    const placeholder = `{{${key}}}`;
    resolvedUrl = resolvedUrl.replace(placeholder, value);
    resolvedBody = resolvedBody.replace(new RegExp(placeholder.replace(/[{}]/g, '\\$&'), 'g'), value);
  }

  console.log('Resolved URL:', resolvedUrl);
  console.log('Resolved body:', JSON.parse(resolvedBody));

  const res = await fetch(resolvedUrl, {
    method,
    headers: { ...headers, 'Content-Type': 'application/json' },
    body: method !== 'GET' ? resolvedBody : undefined,
  });

  console.log('Status:', res.status);
  console.log('Response:', await res.text());
}

// Test with your actual column config and sample row data
await debugHTTPAPIColumn(
  'https://api.hubapi.com/crm/v3/objects/contacts',
  'POST',
  { 'Authorization': 'Bearer your-hubspot-key' },
  { email: '{{Work Email}}', firstname: '{{first_name}}' },
  { 'Work Email': 'test@example.com', 'first_name': 'Jane' },
);
```

### Step 4: Debug Claygent Failures

Common Claygent issues and diagnosis:

```yaml
claygent_debugging:
  empty_results:
    symptom: "Claygent returns empty or 'Could not find information'"
    diagnosis:
      - Test the prompt manually in Clay's Claygent builder (click cell > edit)
      - Try the URL in a browser — is the website accessible?
      - Check if the website blocks bots (CloudFlare challenge page)
    fixes:
      - Use Navigator mode for JavaScript-heavy sites
      - Simplify the prompt to a single question
      - Add fallback sources: "If not on the website, check LinkedIn/Crunchbase"

  inconsistent_results:
    symptom: "Same prompt returns different data each time"
    diagnosis:
      - Claygent uses web search which can vary
      - Dynamic website content changes between requests
    fixes:
      - Make prompts more specific (exact page URL vs general domain)
      - Add structured output format: "Return as JSON with keys: funding_amount, date, investors"

  high_credit_cost:
    symptom: "Claygent consuming too many credits"
    diagnosis:
      - Each Claygent call costs credits + 1 action
      - Running on all rows including low-value ones
    fixes:
      - Add conditional run: "Only run if ICP Score >= 60"
      - Cache results: don't re-run on already-researched companies
```

### Step 5: Build a Support Escalation Package

```markdown
## Clay Support Escalation

**Account:** [your email]
**Plan:** [Starter/Explorer/Pro/Enterprise]
**Date:** [YYYY-MM-DD]

### Issue Description
[One paragraph describing what's broken]

### Impact
- Rows affected: [count]
- Duration: [how long has this been happening]
- Credits impacted: [estimated wasted credits]

### Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Expected result vs actual result]

### Evidence
- Table URL: [link to affected Clay table]
- Screenshot of error cells: [attached]
- Column configuration: [which enrichment, which provider]
- Sample input data that fails: [3-5 rows]
- Sample input data that works: [3-5 rows for comparison]

### What I've Already Tried
1. [Reconnected provider API key]
2. [Tested with different input data]
3. [Checked Clay status page — no incidents reported]
4. [Tested provider API independently — works fine]

### Environment
- Browser: [Chrome/Firefox/Safari + version]
- Plan tier: [with credit balance]
- Provider connections: [list connected providers]

Submit at: https://community.clay.com or support@clay.com
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Intermittent enrichment failures | Provider rate limiting | Reduce concurrent rows, add delay |
| All rows failing suddenly | Provider API key expired | Reconnect in Settings > Connections |
| Partial data returned | Provider has limited coverage | Add waterfall fallback provider |
| HTTP API column timeout | Target API slow | Increase timeout or process async |
| Claygent blocked by website | Bot protection | Use Navigator mode or different data source |

## Resources

- [Clay Community Support](https://community.clay.com)
- [Clay University](https://university.clay.com)

## Next Steps

For high-volume scaling, see `clay-load-scale`.
