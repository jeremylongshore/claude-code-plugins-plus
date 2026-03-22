---
name: apify-debug-bundle
description: |
  Collect Apify debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information about failed Actor runs.
  Trigger: "apify debug", "apify support bundle", "collect apify logs",
  "apify diagnostic", "apify run failed why".
allowed-tools: Read, Bash(curl:*), Bash(npm:*), Bash(node:*), Bash(tar:*), Bash(apify:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, scraping, automation, apify]
compatible-with: claude-code
---

# Apify Debug Bundle

## Overview

Collect all diagnostic information needed to troubleshoot failed Actor runs and prepare Apify support tickets. Pulls run metadata, logs, dataset samples, and environment info into a single bundle.

## Prerequisites

- `apify-client` installed
- `APIFY_TOKEN` configured
- A failed or problematic run ID to investigate

## Instructions

### Step 1: Investigate a Failed Run

```typescript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: process.env.APIFY_TOKEN });

async function investigateRun(runId: string) {
  // Get run details
  const run = await client.run(runId).get();
  console.log('=== Run Summary ===');
  console.log(`Status:       ${run.status}`);
  console.log(`Message:      ${run.statusMessage}`);
  console.log(`Started:      ${run.startedAt}`);
  console.log(`Finished:     ${run.finishedAt}`);
  console.log(`Memory MB:    ${run.options?.memoryMbytes}`);
  console.log(`Timeout sec:  ${run.options?.timeoutSecs}`);
  console.log(`Build:        ${run.buildNumber}`);
  console.log(`Origin:       ${run.meta?.origin}`);
  console.log(`CU used:      ${run.usage?.ACTOR_COMPUTE_UNITS?.toFixed(4)}`);
  console.log(`Cost USD:     $${run.usageTotalUsd?.toFixed(4)}`);

  // Get dataset stats
  if (run.defaultDatasetId) {
    const ds = await client.dataset(run.defaultDatasetId).get();
    console.log(`\nDataset items: ${ds.itemCount}`);
  }

  // Get run log (last 5000 chars)
  const log = await client.run(runId).log().get();
  console.log('\n=== Last 2000 chars of log ===');
  console.log(log?.slice(-2000));

  return { run, log };
}
```

### Step 2: Create Debug Bundle Script

```bash
#!/bin/bash
# apify-debug-bundle.sh <RUN_ID>

RUN_ID="${1:?Usage: apify-debug-bundle.sh <RUN_ID>}"
BUNDLE_DIR="apify-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "Collecting debug info for run $RUN_ID..."

# Environment info
{
  echo "=== Environment ==="
  echo "Date: $(date -u)"
  echo "Node: $(node --version 2>/dev/null || echo 'not found')"
  echo "npm:  $(npm --version 2>/dev/null || echo 'not found')"
  echo ""
  echo "=== Apify Packages ==="
  npm list apify-client apify crawlee 2>/dev/null || echo "No packages found"
  echo ""
  echo "=== Apify CLI ==="
  apify --version 2>/dev/null || echo "CLI not installed"
} > "$BUNDLE_DIR/environment.txt"

# Run details via API
curl -sf -H "Authorization: Bearer $APIFY_TOKEN" \
  "https://api.apify.com/v2/actor-runs/$RUN_ID" | \
  jq '.data | {id, actId, status, statusMessage, startedAt, finishedAt,
    options: {memoryMbytes: .options.memoryMbytes, timeoutSecs: .options.timeoutSecs},
    stats: .stats, usage: .usage, usageTotalUsd}' \
  > "$BUNDLE_DIR/run-details.json" 2>/dev/null

# Run log (secrets auto-redacted by platform)
curl -sf -H "Authorization: Bearer $APIFY_TOKEN" \
  "https://api.apify.com/v2/actor-runs/$RUN_ID/log" \
  > "$BUNDLE_DIR/run-log.txt" 2>/dev/null

# Dataset sample (first 5 items)
DATASET_ID=$(jq -r '.defaultDatasetId // empty' "$BUNDLE_DIR/run-details.json" 2>/dev/null)
if [ -n "$DATASET_ID" ]; then
  curl -sf -H "Authorization: Bearer $APIFY_TOKEN" \
    "https://api.apify.com/v2/datasets/$DATASET_ID/items?limit=5" \
    > "$BUNDLE_DIR/dataset-sample.json" 2>/dev/null
fi

# Key-value store keys
KV_ID=$(jq -r '.defaultKeyValueStoreId // empty' "$BUNDLE_DIR/run-details.json" 2>/dev/null)
if [ -n "$KV_ID" ]; then
  curl -sf -H "Authorization: Bearer $APIFY_TOKEN" \
    "https://api.apify.com/v2/key-value-stores/$KV_ID/keys" \
    > "$BUNDLE_DIR/kv-store-keys.json" 2>/dev/null
fi

# Local config (redacted)
if [ -f .env ]; then
  sed 's/=.*/=***REDACTED***/' .env > "$BUNDLE_DIR/env-redacted.txt"
fi

# Platform health
curl -sf https://api.apify.com/v2/health > "$BUNDLE_DIR/platform-health.json" 2>/dev/null

# Package it up
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo ""
echo "Attach this file to your Apify support ticket."
```

### Step 3: Compare Successful vs Failed Runs

```typescript
async function compareRuns(successId: string, failId: string) {
  const success = await client.run(successId).get();
  const fail = await client.run(failId).get();

  console.log('=== Run Comparison ===');
  const fields = [
    'status', 'buildNumber', 'options.memoryMbytes',
    'options.timeoutSecs', 'stats.requestsFinished',
    'stats.requestsFailed', 'stats.runTimeSecs',
  ] as const;

  console.log(`${'Field'.padEnd(25)} | ${'Success'.padEnd(15)} | Failed`);
  console.log('-'.repeat(60));

  const get = (obj: any, path: string) =>
    path.split('.').reduce((o, k) => o?.[k], obj);

  for (const field of fields) {
    const sVal = get(success, field) ?? 'N/A';
    const fVal = get(fail, field) ?? 'N/A';
    const marker = sVal !== fVal ? ' <--' : '';
    console.log(`${field.padEnd(25)} | ${String(sVal).padEnd(15)} | ${fVal}${marker}`);
  }
}
```

### Step 4: Live Tail Actor Logs

```bash
# Stream logs from a running Actor
RUN_ID="your-run-id"
while true; do
  curl -sf -H "Authorization: Bearer $APIFY_TOKEN" \
    "https://api.apify.com/v2/actor-runs/$RUN_ID/log?stream=1" 2>/dev/null
  sleep 2
done
```

## Sensitive Data Handling

**Always redact before sharing:**
- API tokens (`apify_api_*`)
- Proxy passwords
- PII (emails, names, IPs)
- Custom environment variables

**Safe to include:**
- Run IDs, Actor IDs, dataset IDs
- Error messages and stack traces
- Run configuration (memory, timeout)
- Platform health status

## Escalation Path

1. Check run log for stack trace
2. Compare with a successful run
3. Check [Apify Status](https://status.apify.com) for outages
4. Create debug bundle
5. Submit to [Apify Support](https://console.apify.com/support) with bundle attached

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `Run not found` | Invalid run ID or expired | Unnamed runs expire after 7 days |
| `Log unavailable` | Run still in progress | Wait for completion or stream live |
| Empty dataset | Actor produced no output | Check `failedRequestHandler` in code |
| High CU usage | Memory too high or slow execution | Reduce memory, optimize code |

## Resources

- [Actor Run API](https://docs.apify.com/api/v2/actor-run-get)
- [Run Log API](https://docs.apify.com/api/v2)
- [Apify Support Portal](https://console.apify.com/support)

## Next Steps

For rate limit issues, see `apify-rate-limits`.
