---
name: apple-notes-multi-env-setup
description: |
  Configure Apple Notes automation for multiple accounts and environments.
  Trigger: "apple notes multi account".
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, macos, apple-notes, automation]
compatible-with: claude-code
---

# Apple Notes Multi-Environment Setup

## Multiple Account Configuration
```javascript
// Apple Notes supports multiple accounts simultaneously
const Notes = Application("Notes");
const accounts = Notes.accounts();

// iCloud account (default)
const iCloud = accounts.find(a => a.name() === "iCloud");
// Gmail account
const gmail = accounts.find(a => a.name() === "Gmail");
// On My Mac (local only)
const local = accounts.find(a => a.name() === "On My Mac");

// Target specific account
function createNoteInAccount(accountName, title, body) {
  const account = Notes.accounts().find(a => a.name() === accountName);
  if (!account) throw new Error(`Account ${accountName} not found`);
  const note = Notes.Note({ name: title, body: body });
  account.folders[0].notes.push(note);
  return note.id();
}
```

## Environment-Based Configuration
```typescript
// src/config/environments.ts
interface NotesEnvConfig {
  accountName: string;
  defaultFolder: string;
  autoSync: boolean;
}

const ENVIRONMENTS: Record<string, NotesEnvConfig> = {
  personal: { accountName: "iCloud", defaultFolder: "Personal", autoSync: true },
  work: { accountName: "Gmail", defaultFolder: "Work", autoSync: true },
  local: { accountName: "On My Mac", defaultFolder: "Notes", autoSync: false },
};
```

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [JXA Examples](https://jxa-examples.akjems.com/)
