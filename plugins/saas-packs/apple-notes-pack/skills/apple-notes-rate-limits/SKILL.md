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
Apple Notes does not have API rate limits, but iCloud sync and AppleEvent processing create practical throughput limits.

## Practical Limits
| Operation | Safe Rate | Notes |
|-----------|----------|-------|
| Create note | 1/second | iCloud sync buffer |
| Read note | 10/second | Local operation |
| Search notes | 2/second | Full-text scan |
| Move note | 1/second | Triggers sync |
| Delete note | 1/second | Triggers sync |
| Batch (100 notes) | ~2 minutes | With 1s delays |

## Throttled Operations
```typescript
import { execSync } from "child_process";

async function throttledNoteOps(operations: Array<() => void>, delayMs = 1000) {
  for (const op of operations) {
    op();
    await new Promise(r => setTimeout(r, delayMs));
  }
}
```

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Examples](https://jxa-examples.akjems.com/)
