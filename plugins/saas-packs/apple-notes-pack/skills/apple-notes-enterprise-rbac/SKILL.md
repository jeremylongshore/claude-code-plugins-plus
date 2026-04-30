---
name: apple-notes-enterprise-rbac
description: 'Implement access control for multi-user Apple Notes automation.

  Trigger: "apple notes access control".

  '
allowed-tools: Read, Write, Edit, Bash(osascript:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- macos
- apple-notes
- automation
compatibility: Designed for Claude Code
---
# Apple Notes Enterprise RBAC

## Overview

Apple Notes has no built-in role-based access control (RBAC). In enterprise environments with Managed Apple IDs via Apple Business Manager, administrators control Notes access through MDM (Mobile Device Management) profiles. For multi-user automation scenarios, implement access control at the automation layer using account separation, folder-based permissions, and shared folder restrictions. iCloud Shared Notes (macOS Ventura+) provide basic collaboration, but fine-grained permissions (read-only vs edit) must be enforced in your wrapper code.

## Account-Based Access Control

```javascript
// Apple Notes supports multiple accounts (iCloud, Gmail, On My Mac)
// Use account separation as the primary access boundary
const Notes = Application("Notes");

function getAccountByName(name) {
  const account = Notes.accounts().find(a => a.name() === name);
  if (!account) throw new Error(`Account not found: ${name}`);
  return account;
}

// Audit all accounts and their folder structures
function auditAccounts() {
  return Notes.accounts().map(a => ({
    name: a.name(),
    folders: a.folders().map(f => f.name()),
    noteCount: a.notes().length,
  }));
}

// Restrict automation to a specific account only
const ALLOWED_ACCOUNT = "iCloud";
function safeGetNotes() {
  const account = getAccountByName(ALLOWED_ACCOUNT);
  return account.notes();
}
```

## Folder-Based Permission Model

```typescript
// src/rbac/permissions.ts
interface FolderPermission {
  folder: string;
  allowedRoles: string[];
  operations: ("read" | "write" | "delete")[];
}

const FOLDER_PERMISSIONS: FolderPermission[] = [
  { folder: "Public",    allowedRoles: ["viewer", "editor", "admin"], operations: ["read"] },
  { folder: "Team",      allowedRoles: ["editor", "admin"],          operations: ["read", "write"] },
  { folder: "Sensitive",  allowedRoles: ["admin"],                    operations: ["read", "write", "delete"] },
];

function checkPermission(role: string, folder: string, op: "read" | "write" | "delete"): boolean {
  const perm = FOLDER_PERMISSIONS.find(p => p.folder === folder);
  if (!perm) return false;
  return perm.allowedRoles.includes(role) && perm.operations.includes(op);
}
```

## MDM-Based Enforcement

```bash
# Apple Business Manager + MDM profiles can:
# 1. Disable Notes.app entirely on managed devices
# 2. Restrict iCloud Notes sync (force "On My Mac" only)
# 3. Enforce Managed Apple IDs (separate from personal)

# Check if device is MDM-managed
profiles status -type enrollment 2>/dev/null

# Check Notes restrictions via MDM profile
profiles list -verbose 2>/dev/null | grep -A5 "com.apple.notes"

# Managed Apple IDs cannot:
# - Share notes with personal Apple IDs
# - Use third-party account types (Gmail, Yahoo)
# - Access notes outside the organization's domain
```

## Shared Folder Audit

```javascript
// Audit shared notes (macOS Ventura+ with iCloud sharing)
const Notes = Application("Notes");
const allNotes = Notes.defaultAccount.notes();

// Notes shared via iCloud show as shared in the UI
// JXA does not expose sharing metadata directly
// Workaround: check folder names for "Shared" convention
const sharedFolders = Notes.defaultAccount.folders()
  .filter(f => f.name().toLowerCase().includes("shared"));

sharedFolders.forEach(f => {
  console.log(`Shared folder: ${f.name()} — ${f.notes().length} notes`);
});
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Cannot access Managed Apple ID notes | Personal automation on corporate device | Use the managed account explicitly via `getAccountByName()` |
| Shared folder not visible | iCloud sharing not accepted by recipient | Recipient must accept share invitation in Notes.app |
| MDM blocks osascript | Device restriction profile active | Request IT to allow automation; use Shortcuts as alternative |
| Folder permissions bypass | JXA has full access once TCC approved | Enforce permissions in your wrapper code, not at OS level |
| Multiple accounts create confusion | Notes from wrong account modified | Always specify account explicitly; never use `defaultAccount` in multi-user |

## Resources

- [Apple Business Manager User Guide](https://support.apple.com/guide/apple-business-manager/welcome/web)
- [MDM Protocol Reference](https://developer.apple.com/documentation/devicemanagement)
- [Mac Automation Scripting Guide](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/)

## Next Steps

For multi-account environment configuration, see `apple-notes-multi-env-setup`. For security hardening, see `apple-notes-security-basics`.
