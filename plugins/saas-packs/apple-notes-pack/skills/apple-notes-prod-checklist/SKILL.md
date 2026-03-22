---
name: apple-notes-prod-checklist
description: |
  Production checklist for Apple Notes automation deployments.
  Trigger: "apple notes production checklist".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes Production Checklist

## Pre-Deployment
- [ ] macOS automation permissions granted and tested
- [ ] Notes.app configured to launch at login (if needed)
- [ ] iCloud sync verified working
- [ ] Error handling for all AppleEvent failures
- [ ] Throttling configured (1 op/second for writes)
- [ ] Exported data permissions restricted (chmod 600)
- [ ] Backup strategy for note content documented
- [ ] Script tested on target macOS version

## Validation
```bash
#!/bin/bash
echo "=== Apple Notes Readiness ==="
echo -n "[$(pgrep -x Notes > /dev/null && echo PASS || echo FAIL)] Notes.app running"
echo ""
echo -n "[$(osascript -l JavaScript -e "Application(\"Notes\").defaultAccount.notes.length" 2>/dev/null && echo PASS || echo FAIL)] Notes accessible"
echo ""
echo -n "[$(sw_vers -productVersion | grep -q "^1[3-9]" && echo PASS || echo WARN)] macOS 13+"
echo ""
echo "=== Done ==="
```

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Examples](https://jxa-examples.akjems.com/)
