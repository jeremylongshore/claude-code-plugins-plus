---
name: fathom-debug-bundle
description: 'Collect Fathom API diagnostics for support cases.

  Trigger with phrases like "fathom debug", "fathom diagnostics".

  '
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- meeting-intelligence
- ai-notes
- fathom
compatibility: Designed for Claude Code
---
# Fathom Debug Bundle

## Overview

Collect Fathom API connectivity status, meeting recording metadata, transcript availability, and authentication state into a single diagnostic archive. This bundle helps troubleshoot missing transcripts, failed meeting syncs, webhook delivery issues, and API authentication problems. Attach the output to Fathom support tickets so engineers can diagnose integration failures without back-and-forth.

## Debug Collection Script

```bash
#!/bin/bash
set -euo pipefail
BUNDLE="debug-fathom-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

# Environment check
echo "=== Fathom Debug Bundle ===" | tee "$BUNDLE/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE/summary.txt"
echo "FATHOM_API_KEY: ${FATHOM_API_KEY:+[SET]}" >> "$BUNDLE/summary.txt"

# API connectivity
HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "X-Api-Key: ${FATHOM_API_KEY}" \
  https://api.fathom.ai/external/v1/meetings?limit=1 2>/dev/null || echo "000")
echo "API Status: HTTP $HTTP" >> "$BUNDLE/summary.txt"

# Recent meetings (last 5)
curl -s -H "X-Api-Key: ${FATHOM_API_KEY}" \
  "https://api.fathom.ai/external/v1/meetings?limit=5" \
  > "$BUNDLE/recent-meetings.json" 2>&1 || true

# Check transcript availability for latest meeting
MEETING_ID=$(curl -s -H "X-Api-Key: ${FATHOM_API_KEY}" \
  "https://api.fathom.ai/external/v1/meetings?limit=1" 2>/dev/null \
  | jq -r '.meetings[0].id // empty' 2>/dev/null || true)
if [ -n "$MEETING_ID" ]; then
  curl -s -H "X-Api-Key: ${FATHOM_API_KEY}" \
    "https://api.fathom.ai/external/v1/meetings/$MEETING_ID/transcript" \
    > "$BUNDLE/latest-transcript-status.json" 2>&1 || true
fi

# Rate limit headers
curl -s -D "$BUNDLE/rate-headers.txt" -o /dev/null \
  -H "X-Api-Key: ${FATHOM_API_KEY}" \
  https://api.fathom.ai/external/v1/meetings?limit=1 2>/dev/null || true

tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Analyzing the Bundle

```bash
tar -xzf debug-fathom-*.tar.gz
cat debug-fathom-*/summary.txt                    # API auth + connectivity
jq '.meetings[] | {id, title, created_at}' debug-fathom-*/recent-meetings.json
grep -i "ratelimit\|retry" debug-fathom-*/rate-headers.txt
```

## Common Issues

| Symptom | Check in Bundle | Fix |
|---------|----------------|-----|
| API returns 401 | `summary.txt` shows HTTP 401 | Regenerate API key in Fathom Settings > Integrations |
| Meetings list empty | `recent-meetings.json` has no entries | Verify Fathom recorder joined meetings; check calendar integration |
| Transcript unavailable | `latest-transcript-status.json` shows processing state | Wait for processing to complete (typically 5-15 min after meeting ends) |
| Rate limited (429) | `rate-headers.txt` shows Retry-After header | Reduce polling frequency; implement exponential backoff |
| Webhook not firing | `summary.txt` shows API is reachable but no data | Verify webhook URL in Fathom dashboard; check endpoint returns 200 |

## Automated Health Check

```typescript
async function checkFathom(): Promise<void> {
  const key = process.env.FATHOM_API_KEY;
  if (!key) { console.error("[FAIL] FATHOM_API_KEY not set"); return; }

  const res = await fetch("https://api.fathom.ai/external/v1/meetings?limit=1", {
    headers: { "X-Api-Key": key },
  });
  console.log(`[${res.ok ? "OK" : "FAIL"}] API: HTTP ${res.status}`);

  if (res.ok) {
    const data = await res.json();
    console.log(`[INFO] Meetings accessible: ${data.meetings?.length ?? 0} returned`);
  }
  const remaining = res.headers.get("x-ratelimit-remaining");
  if (remaining) console.log(`[INFO] Rate limit remaining: ${remaining}`);
}
checkFathom();
```

## Resources

- [Fathom Status](https://status.fathom.video)

## Next Steps

See `fathom-common-errors` for transcript sync and webhook troubleshooting patterns.
