---
name: flyio-debug-bundle
description: 'Collect Fly.io debug evidence for support tickets including machine
  status,

  logs, health checks, volume state, and networking diagnostics.

  Trigger: "fly.io debug", "fly.io support", "fly.io diagnostic", "fly doctor".

  '
allowed-tools: Read, Bash(fly:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- edge-compute
- flyio
compatibility: Designed for Claude Code
---
# Fly.io Debug Bundle

## Overview

Collect machine state, app health, volume status, deploy history, network connectivity, and platform diagnostics into a single archive for Fly.io support tickets. This bundle captures everything needed to troubleshoot stuck deployments, machine boot failures, volume corruption, and edge networking problems.

## Debug Collection Script

```bash
#!/bin/bash
set -euo pipefail
APP="${1:?Usage: fly-debug.sh <app-name>}"
BUNDLE="debug-flyio-${APP}-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

# Environment check
echo "=== Fly.io Debug Bundle: $APP ===" | tee "$BUNDLE/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE/summary.txt"
echo "FLY_API_TOKEN: ${FLY_API_TOKEN:+[SET]}" >> "$BUNDLE/summary.txt"
echo "flyctl: $(fly version 2>/dev/null || echo 'not found')" >> "$BUNDLE/summary.txt"

# API connectivity
HTTP=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${FLY_API_TOKEN}" \
  https://api.machines.dev/v1/apps 2>/dev/null || echo "000")
echo "Machines API: HTTP $HTTP" >> "$BUNDLE/summary.txt"

# App status and machine state
fly status -a "$APP" > "$BUNDLE/status.txt" 2>&1 || true
fly machine list -a "$APP" --json > "$BUNDLE/machines.json" 2>&1 || true

# Recent logs (last 200 lines)
fly logs -a "$APP" --no-tail 2>&1 | tail -200 > "$BUNDLE/logs.txt" || true

# Volumes, releases, and doctor
fly volumes list -a "$APP" > "$BUNDLE/volumes.txt" 2>&1 || true
fly releases -a "$APP" > "$BUNDLE/releases.txt" 2>&1 || true
fly doctor > "$BUNDLE/doctor.txt" 2>&1 || true

# Network and platform status
curl -s -o /dev/null -w "App endpoint: HTTP %{http_code}\n" \
  "https://${APP}.fly.dev/" >> "$BUNDLE/summary.txt" 2>/dev/null || echo "App: unreachable" >> "$BUNDLE/summary.txt"
curl -s https://status.flyio.net/api/v2/status.json 2>/dev/null | \
  jq -r '"Platform: " + .status.description' >> "$BUNDLE/summary.txt" || true

tar -czf "$BUNDLE.tar.gz" "$BUNDLE" && rm -rf "$BUNDLE"
echo "Bundle: $BUNDLE.tar.gz"
```

## Analyzing the Bundle

```bash
tar -xzf debug-flyio-*.tar.gz
cat debug-flyio-*/summary.txt                 # Quick health overview
jq '.[] | {id, state, region}' debug-flyio-*/machines.json  # Machine states
grep -i "error\|fail\|crash" debug-flyio-*/logs.txt         # Error patterns
cat debug-flyio-*/doctor.txt                  # Fly.io self-diagnosis
```

## Common Issues

| Symptom | Check in Bundle | Fix |
|---------|----------------|-----|
| Machine stuck in `created` state | `machines.json` shows state != `started` | `fly machine start <id>` or destroy and redeploy |
| Deploy hangs indefinitely | `releases.txt` shows failed release | Check `logs.txt` for health check timeout; increase `[http_service.concurrency]` |
| Volume not mounting | `volumes.txt` shows volume in wrong region | Create volume in same region as machine; only one machine can mount a volume |
| App returns 502 | `summary.txt` shows app unreachable | Check `logs.txt` for process crash; verify internal port matches `fly.toml` |
| DNS not resolving | `doctor.txt` shows DNS warnings | Run `fly ips list`; ensure A/AAAA records exist; check custom domain CNAME |

## Automated Health Check

```typescript
async function checkFlyio(): Promise<void> {
  const token = process.env.FLY_API_TOKEN;
  if (!token) { console.error("[FAIL] FLY_API_TOKEN not set"); return; }

  const res = await fetch("https://api.machines.dev/v1/apps", {
    headers: { Authorization: `Bearer ${token}` },
  });
  console.log(`[${res.ok ? "OK" : "FAIL"}] Machines API: HTTP ${res.status}`);

  if (res.ok) console.log("[INFO] Machines API accessible");
}
checkFlyio();
```

## Resources

- [Fly.io Status](https://status.flyio.net/)

## Next Steps

See `flyio-common-errors`.
