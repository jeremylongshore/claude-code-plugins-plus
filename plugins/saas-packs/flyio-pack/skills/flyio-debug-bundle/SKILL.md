---
name: flyio-debug-bundle
description: |
  Collect Fly.io debug evidence for support tickets including machine status,
  logs, health checks, volume state, and networking diagnostics.
  Trigger: "fly.io debug", "fly.io support", "fly.io diagnostic", "fly doctor".
allowed-tools: Read, Bash(fly:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, edge-compute, flyio]
compatible-with: claude-code
---

# Fly.io Debug Bundle

## Overview

Collect diagnostic information for Fly.io support tickets. Captures app status, machine state, recent logs, volume health, and network connectivity.

## Instructions

```bash
#!/bin/bash
# fly-debug.sh — Usage: bash fly-debug.sh my-app
set -euo pipefail
APP="${1:?Usage: fly-debug.sh <app-name>}"
BUNDLE="fly-debug-${APP}-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

echo "=== Fly.io Debug Bundle: $APP ===" | tee "$BUNDLE/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE/summary.txt"
echo "flyctl: $(fly version)" >> "$BUNDLE/summary.txt"

# App status
fly status -a "$APP" > "$BUNDLE/status.txt" 2>&1 || true

# Machine details
fly machine list -a "$APP" --json > "$BUNDLE/machines.json" 2>&1 || true

# Recent logs (last 100 lines)
fly logs -a "$APP" --no-tail 2>&1 | tail -100 > "$BUNDLE/logs.txt" || true

# Volumes
fly volumes list -a "$APP" > "$BUNDLE/volumes.txt" 2>&1 || true

# Releases / deploy history
fly releases -a "$APP" > "$BUNDLE/releases.txt" 2>&1 || true

# fly doctor
fly doctor > "$BUNDLE/doctor.txt" 2>&1 || true

# Network check
echo -n "App reachable: " >> "$BUNDLE/summary.txt"
curl -s -o /dev/null -w "%{http_code}" "https://${APP}.fly.dev/" >> "$BUNDLE/summary.txt" 2>/dev/null
echo "" >> "$BUNDLE/summary.txt"

# Platform status
echo -n "Platform: " >> "$BUNDLE/summary.txt"
curl -s https://status.flyio.net/api/v2/status.json 2>/dev/null | \
  jq -r '.status.description' >> "$BUNDLE/summary.txt" || echo "unreachable" >> "$BUNDLE/summary.txt"

# Package
tar -czf "$BUNDLE.tar.gz" "$BUNDLE"
rm -rf "$BUNDLE"
echo "Bundle created: $BUNDLE.tar.gz"
```

## Resources

- [Fly.io Status](https://status.flyio.net/)
- [Fly.io Community](https://community.fly.io/)

## Next Steps

For rate limit issues, see `flyio-rate-limits`.
