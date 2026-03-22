---
name: apple-notes-cost-tuning
description: |
  Apple Notes cost optimization — it is free, focus on iCloud storage management.
  Trigger: "apple notes cost".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes Cost Tuning

## Overview
Apple Notes is free. The only cost is iCloud storage, which is shared across all Apple services.

## iCloud Storage Tiers
| Plan | Storage | Price/mo | Notes Capacity |
|------|---------|----------|----------------|
| Free | 5 GB | $0 | ~50,000 text notes |
| iCloud+ 50GB | 50 GB | $0.99 | Effectively unlimited |
| iCloud+ 200GB | 200 GB | $2.99 | Effectively unlimited |
| iCloud+ 2TB | 2 TB | $9.99 | Effectively unlimited |

## Storage Optimization
```bash
# Check Notes storage usage
osascript -l JavaScript -e "
  const Notes = Application(\"Notes\");
  const notes = Notes.defaultAccount.notes();
  let totalChars = 0;
  notes.forEach(n => { totalChars += n.body().length; });
  \`${notes.length} notes, ~${Math.round(totalChars / 1024)}KB of text content\`;
"

# Large notes (>100KB body — usually have embedded images)
osascript -l JavaScript -e "
  const Notes = Application(\"Notes\");
  Notes.defaultAccount.notes()
    .filter(n => n.body().length > 100000)
    .map(n => \`\${n.name()} (${Math.round(n.body().length/1024)}KB)\`)
    .join(\"\\n\");
"
```

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Examples](https://jxa-examples.akjems.com/)
