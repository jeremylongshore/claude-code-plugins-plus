---
name: apple-notes-reference-architecture
description: |
  Reference architecture for Apple Notes automation systems.
  Trigger: "apple notes architecture".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes Reference Architecture

## Architecture
```
┌────────────────────────────────────────────────┐
│                macOS Machine                     │
│                                                  │
│  ┌──────────┐   ┌───────────┐   ┌────────────┐ │
│  │ Your App │──▶│ osascript  │──▶│ Notes.app  │ │
│  │ (Node.js)│   │ (JXA/AS)  │   │ (iCloud)   │ │
│  └──────────┘   └───────────┘   └────────────┘ │
│       │                               │          │
│  ┌────▼─────┐                  ┌──────▼───────┐ │
│  │ SQLite   │                  │ iCloud Sync  │ │
│  │ Cache    │                  │ (automatic)  │ │
│  └──────────┘                  └──────────────┘ │
└────────────────────────────────────────────────┘
```

## Project Structure
```
apple-notes-automation/
├── src/
│   ├── notes-client.ts       # JXA wrapper class
│   ├── templates/             # Note templates
│   ├── export/                # Export to MD/JSON/SQLite
│   ├── events/                # Change detection polling
│   └── server.ts              # Optional: local API server
├── scripts/
│   ├── notes-cli.sh           # CLI wrapper
│   ├── export-all.sh          # Full export script
│   └── template-create.js     # JXA template engine
├── tests/
│   ├── mocks/                 # Mock client for CI
│   └── unit/                  # Unit tests
└── package.json
```

## Key Constraints
| Constraint | Impact | Workaround |
|-----------|--------|------------|
| macOS only | No Linux/Windows | Run on Mac; export for cross-platform |
| No REST API | Cannot access remotely | Local-only; export to portable format |
| iCloud sync lag | Writes may not appear instantly | Poll with delay |
| No webhooks | Cannot push events | Poll for changes |
| HTML-only body | No native Markdown | Convert on export |

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Examples](https://jxa-examples.akjems.com/)
