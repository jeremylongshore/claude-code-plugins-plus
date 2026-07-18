# Apify Debug Bundle — Full Implementation

Complete, copy-pasteable implementations for each step of the debug-bundle
workflow. The SKILL.md carries the lean skeleton; this file carries the full
detail.

## Step 1: Investigate a Failed Run

Pull run metadata, dataset stats, and the tail of the run log through the
`apify-client` SDK.

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

## Step 2: Create Debug Bundle Script

Collect environment info, run details, log, dataset sample, key-value store
keys, redacted local config, and platform health into a single tarball ready
to attach to a support ticket. All API calls authenticate with the
`APIFY_TOKEN` Bearer header; the platform auto-redacts secrets in run logs.

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

## Step 3: Compare Successful vs Failed Runs

Diff two runs field-by-field to spot the configuration or stats delta that
explains the failure. Differing fields are flagged with a `<--` marker.

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

## Step 4: Live Tail Actor Logs

Stream logs from a still-running Actor when the log endpoint is not yet final.

```bash
# Stream logs from a running Actor
RUN_ID="your-run-id"
while true; do
  curl -sf -H "Authorization: Bearer $APIFY_TOKEN" \
    "https://api.apify.com/v2/actor-runs/$RUN_ID/log?stream=1" 2>/dev/null
  sleep 2
done
```
