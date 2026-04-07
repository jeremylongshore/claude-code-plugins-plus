---
name: apple-notes-rate-limits
description: |
  Handle Apple Notes automation rate limits and iCloud sync throttling.
  Trigger: "apple notes rate limit".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes Rate Limits

## Overview

Apple Notes has no formal API rate limits like cloud services do. However, there are practical throughput limits imposed by three systems: the Apple Events IPC bridge (osascript to Notes.app), the iCloud sync daemon (`bird`/`cloudd`) that must process each write, and the Notes.app SQLite database that handles concurrent access. Exceeding these practical limits causes timeouts (-1712), sync lag, or data loss when writes outpace iCloud's upload buffer. This guide documents safe operation rates and provides throttling patterns.

## Practical Rate Limits

| Operation | Safe Rate | Bottleneck | Exceeding Limit |
|-----------|----------|------------|-----------------|
| Create note | 1/second | iCloud sync buffer | Sync lag; notes missing on other devices |
| Read note (name/body) | 10/second | Apple Events IPC | -1712 timeout errors |
| Search (`.whose()`) | 2/second | Notes.app indexer | UI freeze; timeout |
| Move note between folders | 1/second | iCloud + local DB | Folder state inconsistency |
| Delete note | 1/second | iCloud delete propagation | Deleted notes reappear |
| Bulk list (all notes) | 1/10 seconds | Memory + IPC | Process killed by macOS |
| Attachment operations | 1/5 seconds | File I/O + sync | Corrupt or missing attachments |

## Throttled Operation Queue

```typescript
// src/rate-limit/throttle.ts
import { execSync } from "child_process";

interface ThrottleConfig {
  minDelayMs: number;
  maxRetries: number;
  backoffMultiplier: number;
}

const THROTTLE_CONFIGS: Record<string, ThrottleConfig> = {
  read:   { minDelayMs: 100,  maxRetries: 3, backoffMultiplier: 2 },
  write:  { minDelayMs: 1000, maxRetries: 5, backoffMultiplier: 2 },
  delete: { minDelayMs: 1000, maxRetries: 3, backoffMultiplier: 3 },
  search: { minDelayMs: 500,  maxRetries: 2, backoffMultiplier: 2 },
};

async function throttledExec<T>(
  operation: () => T,
  type: keyof typeof THROTTLE_CONFIGS = "write"
): Promise<T> {
  const config = THROTTLE_CONFIGS[type];
  let delay = config.minDelayMs;

  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      const result = operation();
      await new Promise(r => setTimeout(r, config.minDelayMs));
      return result;
    } catch (e: any) {
      if (attempt === config.maxRetries) throw e;
      console.warn(`Retry ${attempt + 1}/${config.maxRetries} after ${delay}ms: ${e.message}`);
      await new Promise(r => setTimeout(r, delay));
      delay *= config.backoffMultiplier;
    }
  }
  throw new Error("Unreachable");
}
```

## Batch Operations with Rate Limiting

```bash
#!/bin/bash
# Batch create notes with throttling
INPUT_FILE="$1"  # JSON array of {title, body} objects
DELAY=1  # seconds between creates

jq -c '.[]' "$INPUT_FILE" | while IFS= read -r note; do
  title=$(echo "$note" | jq -r '.title')
  body=$(echo "$note" | jq -r '.body')
  osascript -l JavaScript -e "
    const Notes = Application('Notes');
    const n = Notes.Note({name: '$title', body: '$body'});
    Notes.defaultAccount.folders[0].notes.push(n);
    n.name();
  " && echo "Created: $title" || echo "FAILED: $title"
  sleep "$DELAY"
done
```

## iCloud Sync Monitoring During Bulk Operations

```bash
# Monitor iCloud sync backlog during batch operations
watch -n 5 'echo "=== Sync Status ===";
  brctl status com.apple.Notes 2>/dev/null || echo "brctl unavailable";
  echo ""; echo "=== Note Count ===";
  osascript -l JavaScript -e "Application(\"Notes\").defaultAccount.notes.length" 2>/dev/null'
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| -1712 AppleEvent timeout | Operations sent faster than Notes can process | Increase delay between operations; use throttled queue |
| Notes reappear after deletion | iCloud sync restored note before delete propagated | Wait 5s after delete; verify deletion on another device |
| Duplicate notes created | Retry on timeout re-executed successful create | Track created note IDs; check before retry |
| iCloud sync stops during bulk ops | Sync daemon overwhelmed | Pause operations for 30s; `killall bird` to restart sync |
| UI becomes unresponsive | Too many Apple Events queued | Reduce concurrency; add `delay(2)` in JXA scripts |

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [Apple Events Programming Guide](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/ScriptableCocoaApplications/)
- [iCloud Sync Architecture](https://support.apple.com/en-us/102651)

## Next Steps

For performance optimization beyond throttling, see `apple-notes-performance-tuning`. For monitoring sync health during operations, see `apple-notes-observability`.
