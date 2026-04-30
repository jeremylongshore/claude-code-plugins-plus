---
name: apple-notes-observability
description: 'Monitor Apple Notes automation health and performance metrics.

  Trigger: "apple notes monitoring".

  '
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- macos
- apple-notes
- automation
compatibility: Designed for Claude Code
---
# Apple Notes Observability

## Overview

Apple Notes has no built-in metrics API or health endpoint. Observability must be built from the outside: polling note counts and folder states via JXA, monitoring iCloud sync daemon health, tracking osascript response latency, and watching system logs for Notes-related errors. This guide sets up a lightweight monitoring stack using bash scripts, structured JSON logs, and macOS notifications for alerting. For persistent monitoring, deploy the health check as a launchd agent that runs on a schedule.

## Health Check Script

```bash
#!/bin/bash
# scripts/notes-health-check.sh — Deploy via launchd (every 5 minutes)
LOG_FILE="${NOTES_LOG_DIR:-/tmp}/notes-health.jsonl"

timestamp=$(date -Iseconds)
notes_running=$(pgrep -x Notes > /dev/null && echo "true" || echo "false")

# Measure JXA latency
start_ms=$(($(date +%s%N)/1000000))
note_count=$(osascript -l JavaScript -e 'Application("Notes").defaultAccount.notes.length' 2>/dev/null || echo "-1")
folder_count=$(osascript -l JavaScript -e 'Application("Notes").defaultAccount.folders.length' 2>/dev/null || echo "-1")
account_count=$(osascript -l JavaScript -e 'Application("Notes").accounts().length' 2>/dev/null || echo "-1")
end_ms=$(($(date +%s%N)/1000000))
latency_ms=$((end_ms - start_ms))

# iCloud sync daemon status
bird_running=$(pgrep -x bird > /dev/null && echo "true" || echo "false")
cloudd_running=$(pgrep -x cloudd > /dev/null && echo "true" || echo "false")

# Determine health
healthy="true"
[ "$notes_running" = "false" ] && healthy="false"
[ "$note_count" = "-1" ] && healthy="false"
[ "$latency_ms" -gt 10000 ] && healthy="false"

echo "{\"ts\":\"$timestamp\",\"running\":$notes_running,\"notes\":$note_count,\"folders\":$folder_count,\"accounts\":$account_count,\"latency_ms\":$latency_ms,\"bird\":$bird_running,\"cloudd\":$cloudd_running,\"healthy\":$healthy}" >> "$LOG_FILE"

# Alert on unhealthy state
if [ "$healthy" = "false" ]; then
  osascript -e "display notification \"Notes health check failed (notes=$note_count, latency=${latency_ms}ms)\" with title \"Notes Alert\""
fi
```

## Metrics Dashboard (CLI)

```bash
#!/bin/bash
# scripts/notes-dashboard.sh — Quick view of recent health data
LOG_FILE="${NOTES_LOG_DIR:-/tmp}/notes-health.jsonl"

echo "=== Apple Notes Health Dashboard ==="
echo "Last 10 checks:"
tail -10 "$LOG_FILE" | jq -r '"\(.ts) | notes=\(.notes) | folders=\(.folders) | latency=\(.latency_ms)ms | healthy=\(.healthy)"'

echo ""
echo "=== Trend (note count, last 24h) ==="
# Show note count changes
awk -F'"notes":' '{split($2,a,","); print a[1]}' "$LOG_FILE" | tail -48 | sort -u

echo ""
echo "=== Alerts (unhealthy checks) ==="
grep '"healthy":false' "$LOG_FILE" | tail -5 | jq -r '"\(.ts): notes=\(.notes), latency=\(.latency_ms)ms"'
```

## Structured Metrics Collection

```typescript
// src/observability/metrics.ts
import { execSync } from "child_process";
import { appendFileSync } from "fs";

interface NotesMetrics {
  timestamp: string;
  noteCount: number;
  folderCount: number;
  accountCount: number;
  latencyMs: number;
  healthy: boolean;
  icloudSyncActive: boolean;
}

function collectMetrics(): NotesMetrics {
  const start = Date.now();
  try {
    const output = execSync(
      `osascript -l JavaScript -e 'JSON.stringify({n: Application("Notes").defaultAccount.notes.length, f: Application("Notes").defaultAccount.folders.length, a: Application("Notes").accounts().length})'`,
      { encoding: "utf8", timeout: 15000 }
    );
    const data = JSON.parse(output);
    const bird = execSync("pgrep -x bird > /dev/null && echo 1 || echo 0", { encoding: "utf8" }).trim();
    return {
      timestamp: new Date().toISOString(), noteCount: data.n, folderCount: data.f,
      accountCount: data.a, latencyMs: Date.now() - start, healthy: true,
      icloudSyncActive: bird === "1",
    };
  } catch {
    return {
      timestamp: new Date().toISOString(), noteCount: 0, folderCount: 0,
      accountCount: 0, latencyMs: Date.now() - start, healthy: false,
      icloudSyncActive: false,
    };
  }
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Latency spikes >10s | Notes.app indexing or large iCloud sync | Transient; alert only if sustained over 3 consecutive checks |
| Note count drops to 0 | iCloud account signed out or TCC revoked | Check `defaults read MobileMeAccounts`; re-authenticate |
| `bird` process not running | iCloud daemon crashed | `killall bird` triggers automatic restart by launchd |
| Health check script fails | `osascript` timeout | Add `timeout 15` prefix to osascript calls |
| Log file grows unbounded | No rotation configured | Add `logrotate` config or truncate weekly via launchd |

## Resources

- [macOS Unified Logging](https://developer.apple.com/documentation/os/logging)
- [launchd.plist Reference](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)
- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)

## Next Steps

For alerting on incidents detected by monitoring, see `apple-notes-incident-runbook`. For performance optimization when metrics show slowdowns, see `apple-notes-performance-tuning`.
