---
name: vercel-common-errors
description: |
  Diagnose and fix common Vercel deployment and function errors.
  Use when encountering Vercel errors, debugging failed deployments,
  or troubleshooting serverless function issues.
  Trigger with phrases like "vercel error", "fix vercel",
  "vercel not working", "debug vercel", "vercel 500", "vercel build failed".
allowed-tools: Read, Grep, Bash(vercel:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, debugging, errors]

---
# Vercel Common Errors

## Overview
Diagnose and resolve the most common Vercel errors across three layers: build pipeline, serverless function runtime, and edge network. Each error includes the error code, root cause, and step-by-step fix.

## Prerequisites
- Vercel CLI installed
- Access to deployment logs (`vercel logs <url>`)
- Access to Vercel dashboard for build logs

## Instructions

### Step 1: Identify the Error Layer
```bash
# Check deployment status and error details
vercel inspect <deployment-url>

# View function runtime logs
vercel logs <deployment-url> --follow

# View build logs via API
curl -s -H "Authorization: Bearer $VERCEL_TOKEN" \
  "https://api.vercel.com/v13/deployments/dpl_xxx" | jq '.state, .errorMessage'
```

**Three error layers:**
1. **Build errors** — appear during `vercel deploy`, exit codes in build log
2. **Runtime errors** — appear when functions are invoked, visible in function logs
3. **Edge/routing errors** — HTTP errors from Vercel's edge network

### Step 2: Build Errors

**`BUILD_FAILED` — Build command exited with non-zero code**
```
Error: Command "npm run build" exited with 1
```
- Check: `vercel.json` → `buildCommand` matches your build script
- Check: all dependencies listed in `package.json` (not just devDependencies for runtime deps)
- Fix: run `npm run build` locally to reproduce

**`MISSING_BUILD_SCRIPT` — No build command found**
```
Error: Missing Build Command
```
- Fix: add `"build"` to `package.json` scripts or set `buildCommand` in vercel.json
- For static sites: set `buildCommand` to empty string or `"true"`

**`FUNCTION_PAYLOAD_TOO_LARGE` — Serverless function bundle > 250 MB**
```
Error: The Serverless Function "api/heavy" is 267 MB which exceeds the maximum size of 250 MB
```
- Fix: add unused packages to `.vercelignore`, use dynamic imports, split into smaller functions
- Check: `@vercel/nft` trace output to see what is being bundled

### Step 3: Runtime Errors

**`FUNCTION_INVOCATION_FAILED` — Unhandled exception in function**
```bash
# View the actual error
vercel logs <deployment-url> --output=short
```
- Common causes: undefined env var, missing database connection, unhandled promise rejection
- Fix: wrap handler in try/catch, verify all env vars are set for the target environment

**`FUNCTION_INVOCATION_TIMEOUT` — Function exceeded max duration**
```
Error: Task timed out after 10.00 seconds
```
- Hobby: 10s max, Pro: 60s default (up to 300s), Enterprise: 900s
- Fix: optimize database queries, add connection pooling, or move to background processing
- Configure in vercel.json:
```json
{
  "functions": {
    "api/slow-endpoint.ts": {
      "maxDuration": 60
    }
  }
}
```

**`NO_RESPONSE_FROM_FUNCTION` — Function didn't return a response**
- Cause: handler has a code path that doesn't call `res.send()`, `res.json()`, or return a Response
- Fix: ensure ALL code paths return a response, including error handlers

**`FUNCTION_THROTTLED` — Too many concurrent function invocations**
- Hobby: 10 concurrent, Pro: 1000 concurrent
- Fix: implement client-side retry with backoff, or upgrade plan

### Step 4: Edge/Routing Errors

**`404 NOT_FOUND`**
- API route 404: verify file is in `api/` or `pages/api/` directory
- Page 404: check `outputDirectory` in vercel.json, verify build output contains the file
- Fix: run `vercel inspect <url>` to see the deployment file listing

**`504 GATEWAY_TIMEOUT`**
- Serverless function exceeded its timeout — same as FUNCTION_INVOCATION_TIMEOUT
- Fix: increase `maxDuration` or optimize function

**`413 REQUEST_ENTITY_TOO_LARGE`**
- Request body exceeds 4.5 MB limit
- Fix: use chunked upload, stream the body, or use presigned URLs for large files

**`DEPLOYMENT_NOT_FOUND`**
- Deployment was deleted or URL is malformed
- Fix: verify the deployment still exists with `vercel ls`

### Step 5: Environment Variable Errors

**`ReferenceError: process is not defined` (Edge Runtime)**
- Cause: using `process.env` in an edge function
- Fix: Edge Functions can read env vars but only those defined at build time. Ensure vars are set.

**Env var undefined in production but works in preview**
- Cause: variable scoped to Preview only, not Production
- Fix: check scopes in **Settings > Environment Variables**, add Production target

```bash
# Check which environments have the variable
vercel env ls | grep DATABASE_URL
```

## Quick Diagnosis Flowchart

```
Error occurred
├── During build? → Check build logs, run `npm run build` locally
├── During function invocation? → Check function logs with `vercel logs`
├── HTTP 404? → Verify file exists in deployment: `vercel inspect`
├── HTTP 500? → Unhandled exception in function code
├── HTTP 504? → Function timeout — increase maxDuration
└── HTTP 429? → Rate limited — implement retry with backoff
```

## Output
- Error layer identified (build, runtime, or edge)
- Root cause diagnosed using logs and inspection
- Fix applied and verified via new deployment
- Prevention measures documented

## Error Handling
| Error Code | HTTP | Layer | Quick Fix |
|-----------|------|-------|-----------|
| `BUILD_FAILED` | — | Build | Run build locally, check deps |
| `FUNCTION_INVOCATION_FAILED` | 500 | Runtime | Check env vars, add try/catch |
| `FUNCTION_INVOCATION_TIMEOUT` | 504 | Runtime | Increase maxDuration in vercel.json |
| `FUNCTION_THROTTLED` | 429 | Runtime | Reduce concurrency or upgrade plan |
| `FUNCTION_PAYLOAD_TOO_LARGE` | 413 | Build | Reduce bundle size |
| `NOT_FOUND` | 404 | Edge | Verify file paths and routes |
| `EDGE_FUNCTION_INVOCATION_FAILED` | 500 | Edge | Remove Node.js APIs from edge code |
| `NO_RESPONSE_FROM_FUNCTION` | 502 | Runtime | Return response from all code paths |

## Resources
- [Vercel Error Codes](https://vercel.com/docs/errors)
- [Function Limitations](https://vercel.com/docs/functions/limitations)
- [Platform Limits](https://vercel.com/docs/limits)
- [Vercel Status Page](https://www.vercel-status.com)
- [Vercel Logs CLI](https://vercel.com/docs/cli/logs)

## Next Steps
For detailed debug bundles, see `vercel-debug-bundle`.
