---
name: apple-notes-security-basics
description: |
  Apply security best practices for Apple Notes automation scripts.
  Trigger: "apple notes security".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes Security Basics

## Security Checklist
- [ ] Scripts run only locally (never expose osascript to network)
- [ ] No note content logged to files (may contain sensitive data)
- [ ] TCC permissions scoped to specific apps only
- [ ] Exported notes stored with appropriate file permissions
- [ ] iCloud account uses 2FA
- [ ] Automation scripts do not hardcode note content

## AppleScript Sandbox Restrictions
```bash
# Apple Notes runs inside the macOS sandbox
# Scripts can only access Notes via Apple Events (not direct file access)
# The Notes database is at ~/Library/Group Containers/group.com.apple.notes/
# Direct database access is NOT recommended (encrypted, undocumented schema)
```

## Safe Export Pattern
```bash
# Export with restricted permissions
osascript -l JavaScript -e "..." > /tmp/notes-export.json
chmod 600 /tmp/notes-export.json
# Process then delete
rm /tmp/notes-export.json
```

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Examples](https://jxa-examples.akjems.com/)
