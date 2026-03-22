---
name: apple-notes-upgrade-migration
description: |
  Migrate Apple Notes automation scripts between macOS versions.
  Trigger: "apple notes upgrade migration".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes Upgrade & Migration

## macOS Version Changes
| macOS Version | Notes Changes | Migration Impact |
|--------------|---------------|-----------------|
| Ventura (13) | Shared notes via iCloud | New sharing API |
| Sonoma (14) | Tags, smart folders | New JXA properties |
| Sequoia (15) | Math in notes, recording | New content types |

## Migration Steps
```bash
# 1. Export all notes before OS upgrade
osascript -l JavaScript -e "
  const Notes = Application(\"Notes\");
  JSON.stringify(Notes.defaultAccount.notes().map(n => ({
    title: n.name(), body: n.body(), folder: n.container().name()
  })));
" > pre-upgrade-backup.json

# 2. Verify after upgrade
osascript -l JavaScript -e "Application(\"Notes\").defaultAccount.notes.length"

# 3. Test all automation scripts
./scripts/notes-cli.sh count
./scripts/notes-cli.sh list
```

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Examples](https://jxa-examples.akjems.com/)
