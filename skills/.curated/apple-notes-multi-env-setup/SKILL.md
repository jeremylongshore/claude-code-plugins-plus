---
name: apple-notes-multi-env-setup
description: 'Configure Apple Notes automation for multiple accounts and environments.

  Trigger: "apple notes multi account".

  '
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- macos
- apple-notes
- automation
compatibility: Designed for Claude Code
---
# Apple Notes Multi-Environment Setup

## Overview

Apple Notes supports multiple accounts simultaneously: iCloud (default), Gmail/Yahoo/AOL via IMAP, Exchange, and the local "On My Mac" account. Each account has isolated folders and notes, making accounts the natural boundary for environment separation. Use this to separate personal vs work notes, production vs development data, or synced vs local-only content. The "On My Mac" account is especially useful for development and testing because it never syncs to iCloud, so experiments stay local.

## Prerequisites

- A written environment map that names the intended account and folder by stable local configuration, not a broad account default.
- Separate test data for development and staging; iCloud folders alone are not an access-control boundary.
- An approval path for creating accounts or folders, especially in managed or shared environments.

## Instructions

1. Resolve the selected environment from an allowlist and fail if it is not explicitly configured.
2. Verify the expected account and folder exist before a write; do not silently create missing production folders.
3. Keep development local where possible, and require an explicit operator choice before a job touches a synchronized account.
4. Log only the environment label and opaque configuration version, never account names, note titles, or bodies.

## Account Discovery

```bash
# List all configured Notes accounts
osascript -l JavaScript -e '
  const Notes = Application("Notes");
  Notes.accounts().map(a =>
    a.name() + " — " + a.notes().length + " notes, " +
    a.folders().map(f => f.name()).join(", ")
  ).join("\n");
'
```

## Environment-Based Configuration

```typescript
// src/config/environments.ts
interface NotesEnvConfig {
  accountName: string;
  defaultFolder: string;
  autoSync: boolean;
  description: string;
}

const ENVIRONMENTS: Record<string, NotesEnvConfig> = {
  production: {
    accountName: "iCloud",
    defaultFolder: "Production",
    autoSync: true,
    description: "Live notes synced across all devices via iCloud",
  },
  staging: {
    accountName: "iCloud",
    defaultFolder: "Staging",
    autoSync: true,
    description: "Test notes visible on other devices for QA",
  },
  development: {
    accountName: "On My Mac",
    defaultFolder: "Dev",
    autoSync: false,
    description: "Local-only notes for development and testing",
  },
};

function getEnv(): string {
  return process.env.NOTES_ENV || "development";
}
```

## Account-Scoped Operations

```javascript
// JXA wrapper that enforces account isolation
const Notes = Application("Notes");

function getAccount(envName) {
  const config = {
    production: "iCloud",
    staging: "iCloud",
    development: "On My Mac",
  };
  const accountName = config[envName] || config.development;
  const account = Notes.accounts().find(a => a.name() === accountName);
  if (!account) throw new Error(`Account "${accountName}" not found. Enable it in Notes > Settings > Accounts.`);
  return account;
}

function getFolder(account, folderName) {
  let folder = account.folders().find(f => f.name() === folderName);
  if (!folder) {
    // Create folder if it does not exist
    folder = Notes.Folder({ name: folderName });
    account.folders.push(folder);
  }
  return folder;
}

function createNote(envName, folderName, title, body) {
  const account = getAccount(envName);
  const folder = getFolder(account, folderName);
  const note = Notes.Note({ name: title, body: body });
  folder.notes.push(note);
  return note.id();
}
```

## Enable "On My Mac" Account

```bash
# "On My Mac" is disabled by default on newer macOS versions
# Enable via Notes preferences:
# Notes > Settings > check "Enable the On My Mac account"

# Verify it is available
osascript -l JavaScript -e '
  const Notes = Application("Notes");
  const local = Notes.accounts().find(a => a.name() === "On My Mac");
  local ? "On My Mac: enabled (" + local.notes().length + " notes)" : "On My Mac: DISABLED";
'
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| "On My Mac" account not found | Disabled in Notes settings | Notes > Settings > enable "On My Mac" account |
| Gmail account shows no notes | IMAP notes not enabled | System Settings > Internet Accounts > Gmail > enable Notes |
| Folder creation fails on Gmail | IMAP accounts have read-only folder structure | Use iCloud or "On My Mac" for custom folders |
| Notes appear in wrong account | `defaultAccount` used instead of explicit account | Always specify account by name; never rely on default |
| Sync conflict between environments | Same iCloud account, different folders | Use distinct folder names per environment (`Prod/`, `Staging/`) |

## Output

Environment selection yields the approved environment label, an account/folder existence check, and a read-only scope confirmation. A failed match blocks mutation and produces a redacted diagnostic that the configuration owner can act on.

## Examples

For local development, select the configured development environment, confirm the `On My Mac` test folder exists, and use synthetic notes only. For production, require a separately reviewed configuration that points to the exact approved folder; if it is absent, stop and ask the owner to create or approve it rather than creating it automatically.

## Resources

- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)
- [Apple Notes Account Settings](https://support.apple.com/guide/notes/add-or-remove-accounts-not4be498e1e/mac)
- [JXA Cookbook](https://github.com/JXA-Cookbook/JXA-Cookbook)

## Next Steps

For access control across accounts, see `apple-notes-enterprise-rbac`. For monitoring account health, see `apple-notes-observability`.
