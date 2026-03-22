---
name: vercel-advanced-troubleshooting
description: |
  Advanced debugging for hard-to-diagnose Vercel issues including cold starts, edge errors, and function tracing.
  Use when standard troubleshooting fails, investigating intermittent failures,
  or preparing evidence for Vercel support escalation.
  Trigger with phrases like "vercel hard bug", "vercel mystery error",
  "vercel intermittent failure", "difficult vercel issue", "vercel deep debug".
allowed-tools: Read, Grep, Bash(vercel:*), Bash(curl:*), Bash(jq:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, debugging, advanced, troubleshooting]

---
# Vercel Advanced Troubleshooting

## Overview
Diagnose hard-to-find Vercel issues: intermittent cold start failures, edge function crashes, region-specific behavior, function bundling problems, and serverless concurrency issues. Uses systematic isolation, request tracing, and Vercel-specific debugging techniques.

## Prerequisites
- Vercel CLI with access to production logs
- Familiarity with `vercel-common-errors` (standard debugging)
- `curl` and `jq` for API inspection
- Access to deployment inspection tools

## Instructions

### Step 1: Request-Level Tracing
```bash
# Trace a single request through Vercel's edge network
curl -v https://yourdomain.com/api/endpoint 2>&1 | grep -E "x-vercel|cf-ray|age|cache"

# Key headers to check:
# x-vercel-id: <region>::<function-id> — which region served the request
# x-vercel-cache: HIT/MISS/STALE — edge cache status
# x-vercel-execution-region: iad1 — function execution region
# age: 45 — seconds since edge cached the response
# x-matched-path: /api/endpoint — routing match result
```

### Step 2: Cold Start Investigation
```typescript
// Instrument cold start timing in your function
let coldStart = true;
const initTime = Date.now();

export default function handler(req, res) {
  const isCold = coldStart;
  coldStart = false;

  const handlerStart = Date.now();
  // ... your logic ...

  res.setHeader('x-cold-start', String(isCold));
  res.setHeader('x-init-duration', String(handlerStart - initTime));
  res.json({
    coldStart: isCold,
    initDuration: isCold ? handlerStart - initTime : 0,
    handlerDuration: Date.now() - handlerStart,
    region: process.env.VERCEL_REGION,
  });
}
```

```bash
# Measure cold start frequency over N requests
for i in $(seq 1 20); do
  curl -s https://yourdomain.com/api/endpoint \
    | jq '{coldStart, initDuration, region}'
  sleep 2  # Wait between requests to allow isolate recycling
done
```

### Step 3: Function Bundle Analysis
```bash
# Check what's being bundled into your function
vercel inspect https://my-app-xxx.vercel.app

# Check function sizes in the deployment
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v13/deployments/dpl_xxx" \
  | jq '.functions | to_entries[] | {path: .key, size: .value.size, regions: .value.regions}'

# Locally — check what @vercel/nft traces for a function
npx @vercel/nft print api/heavy-endpoint.ts 2>/dev/null | head -50
# Shows all files that will be bundled

# Find unexpectedly large dependencies
npx @vercel/nft print api/heavy-endpoint.ts 2>/dev/null \
  | xargs -I {} du -sh {} 2>/dev/null | sort -rh | head -20
```

### Step 4: Region-Specific Debugging
```bash
# Test from different regions to isolate geographic issues
# Use Vercel's deployment URL with region hints
for region in iad1 sfo1 cdg1 hnd1; do
  echo "=== Region: $region ==="
  curl -s -w "HTTP %{http_code} | Time: %{time_total}s\n" \
    -H "x-vercel-ip-country: US" \
    https://yourdomain.com/api/endpoint
done

# Check if the issue is region-dependent
# If latency varies wildly, check:
# 1. Function region vs database region (cross-region latency)
# 2. Edge middleware adding delay
# 3. External API calls from wrong region
```

### Step 5: Edge Function Crash Debugging
```typescript
// Edge functions crash silently on Node.js API usage
// Common crashes and their symptoms:

// Symptom: EDGE_FUNCTION_INVOCATION_FAILED with no error details
// Cause: Using Node.js Buffer, fs, crypto.createHash in edge runtime

// Diagnostic: check if imports are edge-compatible
export const config = { runtime: 'edge' };

export default function handler(request: Request) {
  // This will crash silently:
  // const hash = require('crypto').createHash('sha256');

  // Use Web Crypto instead:
  const encoder = new TextEncoder();
  const data = encoder.encode('test');
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);

  return Response.json({ ok: true });
}
```

```bash
# Check if a module is edge-compatible
npx edge-runtime --eval "import('your-module')" 2>&1
# Errors here mean the module won't work in edge functions
```

### Step 6: Concurrency and Throttling Debug
```bash
# Check current function concurrency limits
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v9/projects/my-app" \
  | jq '{plan: .plan, concurrency: .concurrencyBucketName}'

# Hobby: 10 concurrent, Pro: 1000, Enterprise: 100000

# Load test to find throttling threshold
npx autocannon -c 50 -d 10 https://yourdomain.com/api/endpoint
# Watch for 429 responses indicating FUNCTION_THROTTLED
```

### Step 7: Systematic Isolation
```
Issue persists? Isolate systematically:

1. Does it happen on preview deployments?
   └── No → Production-only env var or domain issue

2. Does it happen with a minimal function?
   └── No → Issue is in your code, not Vercel platform

3. Does it happen in all regions?
   └── No → Region-specific infrastructure issue

4. Does it happen with edge runtime?
   └── No → Node.js-specific issue (cold starts, module compat)

5. Does it happen without middleware?
   └── No → Middleware is interfering — check matcher scope

6. Create minimal reproduction:
   └── api/test.ts with only the failing behavior
   └── Deploy standalone and test
```

### Step 8: Vercel Support Escalation
```bash
# Collect comprehensive evidence
mkdir vercel-debug && cd vercel-debug

# Deployment details
vercel inspect https://yourdomain.com > inspect.txt
vercel logs https://yourdomain.com --limit=200 > logs.txt

# Request trace
curl -v https://yourdomain.com/api/failing-endpoint 2>&1 > curl-trace.txt

# Function analysis
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v13/deployments/dpl_xxx" > deployment.json

# Platform status at time of issue
curl -s "https://www.vercel-status.com/api/v2/summary.json" > status.json

tar czf vercel-debug-$(date +%Y%m%d).tar.gz .
```

## Output
- Request traced through Vercel's edge network with region and cache data
- Cold start frequency and duration quantified
- Function bundle analyzed for size issues
- Issue isolated to specific layer (edge, runtime, region, middleware)
- Evidence bundle ready for support escalation

## Error Handling
| Symptom | Likely Cause | Debug Approach |
|---------|-------------|---------------|
| Intermittent 500 errors | Cold start + unhandled async | Add global error handler, check init code |
| Latency spikes every ~15 min | Function isolate recycling (cold start) | Measure with x-cold-start header |
| Works in preview, fails in prod | Env var scope mismatch | Compare env vars across environments |
| EDGE_FUNCTION_INVOCATION_FAILED | Node.js API in edge runtime | Check imports for Node.js-only modules |
| Function works locally, fails deployed | Missing dependency or env var | Run `vercel build` locally, check output |

## Resources
- [Vercel Error Codes](https://vercel.com/docs/errors)
- [Function Limitations](https://vercel.com/docs/functions/limitations)
- [Edge Runtime API](https://vercel.com/docs/functions/runtimes/edge)
- [Vercel Support](https://vercel.com/support)
- [@vercel/nft](https://github.com/vercel/nft)

## Next Steps
For load testing and scaling, see `vercel-load-scale`.
