---
name: obsidian-enterprise-rbac
description: |
  Implement team vault access patterns and role-based controls.
  Use when managing shared vaults, implementing access controls,
  or building team collaboration features for Obsidian.
  Trigger with phrases like "obsidian team", "obsidian access control",
  "obsidian enterprise", "shared vault permissions".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Obsidian Enterprise RBAC

## Overview
Vault-level access control patterns for Obsidian in team environments. Covers folder-based permissions via `.obsidian-permissions` files, read-only enforcement for shared vaults, plugin allowlisting, and configuration lockdown through restricted mode.

## Prerequisites
- Obsidian desktop app with a shared/synced vault
- Understanding of Obsidian's `.obsidian/` configuration directory
- A sync mechanism in place (Git, Obsidian Sync, or shared filesystem)
- Node.js 18+ for scripted permission enforcement

## Instructions

### Step 1: Define a Permission Model

Create `.obsidian-permissions` at the vault root. This JSON file maps roles to folder access:

```json
{
  "version": 1,
  "roles": {
    "admin": {
      "folders": ["*"],
      "permissions": ["read", "write", "delete", "manage"]
    },
    "editor": {
      "folders": ["projects/*", "shared/*", "templates/*"],
      "permissions": ["read", "write"]
    },
    "viewer": {
      "folders": ["shared/*", "published/*"],
      "permissions": ["read"]
    }
  },
  "users": {
    "alice@company.com": "admin",
    "bob@company.com": "editor",
    "charlie@company.com": "viewer"
  }
}
```

Obsidian itself has no built-in RBAC, so this file is consumed by a custom plugin that intercepts file operations.

### Step 2: Build the Permission Checker Plugin

Create a plugin that reads `.obsidian-permissions` and gates vault operations:

```typescript
import { Plugin, TFile, Notice } from 'obsidian';

interface PermissionConfig {
  version: number;
  roles: Record<string, { folders: string[]; permissions: string[] }>;
  users: Record<string, string>;
}

export default class RBACPlugin extends Plugin {
  private config: PermissionConfig | null = null;
  private currentUser: string = '';

  async onload() {
    await this.loadPermissions();

    // Intercept file modifications
    this.registerEvent(
      this.app.vault.on('modify', (file) => {
        if (!this.canWrite(file.path)) {
          new Notice(`Permission denied: ${file.path} is read-only for your role`);
        }
      })
    );

    // Intercept file creation
    this.registerEvent(
      this.app.vault.on('create', (file) => {
        if (file instanceof TFile && !this.canWrite(file.parent?.path ?? '/')) {
          new Notice(`Permission denied: cannot create files in ${file.parent?.path}`);
          // Move to user's writable area or delete
          this.app.vault.delete(file);
        }
      })
    );
  }

  private async loadPermissions() {
    const permFile = this.app.vault.getAbstractFileByPath('.obsidian-permissions');
    if (permFile instanceof TFile) {
      const content = await this.app.vault.read(permFile);
      this.config = JSON.parse(content);
    }
    // Identify current user from plugin settings or environment
    const data = await this.loadData();
    this.currentUser = data?.userEmail ?? '';
  }

  private canWrite(path: string): boolean {
    if (!this.config || !this.currentUser) return true; // Fail open if no config
    const role = this.config.users[this.currentUser];
    if (!role) return false;
    const roleDef = this.config.roles[role];
    if (!roleDef) return false;
    if (!roleDef.permissions.includes('write')) return false;

    return roleDef.folders.some(pattern => {
      if (pattern === '*') return true;
      const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');
      return regex.test(path);
    });
  }
}
```

### Step 3: Enforce Read-Only Mode on Shared Vaults

For vaults where most users should only read, set restricted mode in `.obsidian/app.json`:

```json
{
  "strictLineBreaks": false,
  "readableLineLength": true,
  "vimMode": false,
  "livePreview": true
}
```

Then in your RBAC plugin, enforce read-only for non-editor roles by overriding the editor:

```typescript
// In onload(), after permission check:
if (!this.canWrite('/')) {
  // Disable editing commands
  this.registerEvent(
    this.app.workspace.on('editor-change', (editor) => {
      // Revert changes for read-only users
      editor.undo();
      new Notice('This vault is read-only for your role.');
    })
  );
}
```

### Step 4: Plugin Allowlisting

Lock down which community plugins can be enabled. Edit `.obsidian/community-plugins.json` to contain only approved plugins:

```json
["obsidian-git", "dataview", "templater-obsidian", "your-rbac-plugin"]
```

Then protect this file from modification by non-admins. In your RBAC plugin, watch for changes:

```typescript
this.registerEvent(
  this.app.vault.on('modify', async (file) => {
    if (file.path === '.obsidian/community-plugins.json') {
      const role = this.config?.users[this.currentUser];
      if (role !== 'admin') {
        // Restore the approved list
        const approved = await this.loadData();
        await this.app.vault.modify(
          file as TFile,
          JSON.stringify(approved.allowedPlugins)
        );
        new Notice('Only admins can modify the plugin allowlist.');
      }
    }
  })
);
```

### Step 5: Configuration Lockdown via Restricted Mode

Obsidian's restricted mode disables all community plugins. For enterprise deployments, combine this with a config lockdown:

```typescript
// Store a hash of critical config files at deploy time
const LOCKED_CONFIGS = [
  '.obsidian/app.json',
  '.obsidian/appearance.json',
  '.obsidian/hotkeys.json',
  '.obsidian/community-plugins.json',
];

async lockdownConfigs() {
  const hashes: Record<string, string> = {};
  for (const path of LOCKED_CONFIGS) {
    const file = this.app.vault.getAbstractFileByPath(path);
    if (file instanceof TFile) {
      const content = await this.app.vault.read(file);
      hashes[path] = await this.hash(content);
    }
  }
  await this.saveData({ ...await this.loadData(), configHashes: hashes });
}

async verifyConfigs(): Promise<string[]> {
  const data = await this.loadData();
  const violations: string[] = [];
  for (const [path, expectedHash] of Object.entries(data.configHashes ?? {})) {
    const file = this.app.vault.getAbstractFileByPath(path);
    if (file instanceof TFile) {
      const content = await this.app.vault.read(file);
      const actual = await this.hash(content);
      if (actual !== expectedHash) {
        violations.push(path);
      }
    }
  }
  return violations;
}

private async hash(content: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(content);
  const buf = await crypto.subtle.digest('SHA-256', data);
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
}
```

Run `verifyConfigs()` on plugin load and periodically. Alert admins if violations are detected.

## Output
- `.obsidian-permissions` file defining roles, folder access, and user mappings
- RBAC plugin that intercepts create/modify/delete operations
- Read-only enforcement for non-editor roles
- Plugin allowlist protection in `community-plugins.json`
- Configuration lockdown with hash verification for critical `.obsidian/` files

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Permission denied on all files | User email not set in plugin settings | Open RBAC plugin settings, enter your email |
| Allowlist keeps resetting | Non-admin edited `community-plugins.json` | Only admins can modify; check audit log |
| Config hash mismatch on every load | Config changed legitimately | Admin runs `lockdownConfigs()` to update hashes |
| Plugin not intercepting writes | Event handler registration failed | Check console for plugin load errors |
| Sync conflicts on `.obsidian-permissions` | Multiple admins editing simultaneously | Use Git with merge strategy or Obsidian Sync |

## Examples

**Team vault with three roles**: Deploy the `.obsidian-permissions` file above. Set each user's email in the RBAC plugin settings. Editors can modify `projects/` and `shared/` folders; viewers can only read `shared/` and `published/`.

**Locked-down training vault**: Set all users to `viewer` role except instructors (`editor`). Lock config files with `lockdownConfigs()`. Students can read all materials but cannot modify notes or install plugins.

**Plugin governance**: Maintain an allowlist of 5 approved plugins in `community-plugins.json`. The RBAC plugin reverts any unauthorized additions. New plugin requests go through admin approval.

## Resources
- [Obsidian Plugin API - Vault Events](https://docs.obsidian.md/Reference/TypeScript+API/Vault)
- [Obsidian Sync for Teams](https://obsidian.md/sync)
- [RBAC Concepts](https://en.wikipedia.org/wiki/Role-based_access_control)
- [Obsidian Git Plugin](https://github.com/denolehov/obsidian-git) -- version control for shared vaults

## Next Steps
For data backup and sync patterns, see `obsidian-data-handling`. For multi-environment testing of RBAC rules, see `obsidian-multi-env-setup`.
