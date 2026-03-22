---
name: apple-notes-observability
description: |
  Monitor Apple Notes automation health and performance metrics.
  Trigger: "apple notes monitoring".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes Observability

## Monitoring Script
```bash
#!/bin/bash
# scripts/notes-health-check.sh — Run via cron or launchd

LOG_FILE="/tmp/notes-health.log"

timestamp=$(date -Iseconds)
notes_running=$(pgrep -x Notes > /dev/null && echo "true" || echo "false")
note_count=$(osascript -l JavaScript -e "Application(\"Notes\").defaultAccount.notes.length" 2>/dev/null || echo "0")
folder_count=$(osascript -l JavaScript -e "Application(\"Notes\").defaultAccount.folders.length" 2>/dev/null || echo "0")

echo "{\"timestamp\":\"$timestamp\",\"running\":$notes_running,\"notes\":$note_count,\"folders\":$folder_count}" >> "$LOG_FILE"

# Alert if Notes not running
if [ "$notes_running" = "false" ]; then
  osascript -e "display notification \"Notes.app is not running\" with title \"Notes Health Alert\""
fi
```

## Metrics Collection
```typescript
// src/observability/metrics.ts
interface NotesMetrics {
  timestamp: string;
  noteCount: number;
  folderCount: number;
  accountCount: number;
  latencyMs: number;
  healthy: boolean;
}

function collectMetrics(): NotesMetrics {
  const start = Date.now();
  try {
    const output = execSync("osascript -l JavaScript -e \"JSON.stringify({notes: Application(\\\"Notes\\\").defaultAccount.notes.length, folders: Application(\\\"Notes\\\").defaultAccount.folders.length, accounts: Application(\\\"Notes\\\").accounts().length})\"", { encoding: "utf8" });
    const data = JSON.parse(output);
    return { timestamp: new Date().toISOString(), noteCount: data.notes, folderCount: data.folders, accountCount: data.accounts, latencyMs: Date.now() - start, healthy: true };
  } catch {
    return { timestamp: new Date().toISOString(), noteCount: 0, folderCount: 0, accountCount: 0, latencyMs: Date.now() - start, healthy: false };
  }
}
```

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Examples](https://jxa-examples.akjems.com/)
