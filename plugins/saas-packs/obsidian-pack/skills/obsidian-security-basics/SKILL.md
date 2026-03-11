---
name: obsidian-security-basics
description: |
  Implement secure Obsidian plugin development practices.
  Use when handling user data, implementing authentication,
  or ensuring plugin security best practices.
  Trigger with phrases like "obsidian security", "secure obsidian plugin",
  "obsidian data protection", "obsidian privacy".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Obsidian Security Basics

## Overview
Security practices for Obsidian plugin development. Plugins run with full access to the vault filesystem and can make network requests -- responsible plugin development requires protecting user data, validating inputs, and managing external connections securely.

## Prerequisites
- Obsidian plugin development environment
- Understanding of Electron security model
- Awareness of Obsidian's plugin guidelines

## Instructions

### Step 1: Never Store Credentials in Vault Files

Plugin settings are stored as JSON in the vault's `.obsidian/plugins/` directory. This is synced by many cloud services.

```typescript
// BAD: API key stored in plugin settings (synced to cloud)
interface BadSettings {
  apiKey: string;  // Synced to iCloud, Google Drive, etc.
}

// GOOD: use system keychain or prompt each session
import { Platform } from 'obsidian';

async function storeSecurely(key: string, value: string): Promise<void> {
  if (Platform.isDesktopApp) {
    // Use Electron's safeStorage (encrypted at OS level)
    const { safeStorage } = require('electron').remote;
    const encrypted = safeStorage.encryptString(value);
    await plugin.saveData({ encryptedKey: encrypted.toString('base64') });
  }
}
```

### Step 2: Validate All External Data

Data from HTTP requests, clipboard, or URI handlers must be validated.

```typescript
function sanitizeExternalContent(content: string): string {
  // Strip HTML to prevent XSS in preview
  content = content.replace(/<script[^>]*>.*?<\/script>/gi, '');
  content = content.replace(/<iframe[^>]*>.*?<\/iframe>/gi, '');
  content = content.replace(/on\w+="[^"]*"/gi, '');
  // Limit length
  if (content.length > 100000) {
    content = content.substring(0, 100000);
  }
  return content;
}

// Validate URI handler parameters
this.registerObsidianProtocolHandler('myplugin', async (params) => {
  const action = params.action;
  if (!['open', 'create', 'search'].includes(action)) {
    new Notice('Invalid action');
    return;
  }
  // Sanitize file paths to prevent directory traversal
  const path = params.path?.replace(/\.\./g, '');
  if (path) await handleAction(action, path);
});
```

### Step 3: Secure Network Requests

Always use HTTPS and validate responses.

```typescript
async function secureFetch(url: string): Promise<any> {
  // Enforce HTTPS
  if (!url.startsWith('https://')) {
    throw new Error('Only HTTPS requests allowed');
  }
  const response = await requestUrl({
    url,
    method: 'GET',
    headers: { 'User-Agent': 'ObsidianPlugin/1.0' }
  });
  if (response.status !== 200) {
    throw new Error(`HTTP ${response.status}`);
  }
  return response.json;
}
```

### Step 4: Permission Minimization

Only request the permissions your plugin actually needs.

```typescript
// In manifest.json
{
  "isDesktopOnly": false,
  // Don't access filesystem beyond vault unless necessary
  // Don't make network requests unless core to functionality
  // Document WHY you need each permission in README
}

// At runtime: check before accessing sensitive APIs
if (this.app.vault.adapter instanceof FileSystemAdapter) {
  // Desktop-only file operations
  const basePath = this.app.vault.adapter.getBasePath();
  // Never access files outside basePath
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| API key synced to cloud | Stored in plugin settings | Use OS keychain or encrypted storage |
| XSS in note preview | Unsanitized external content | Strip HTML/JS from external data |
| Directory traversal | Unvalidated file paths | Remove `..` from paths, validate against vault |
| HTTP data leak | Using HTTP instead of HTTPS | Enforce HTTPS for all requests |

## Examples

### Content Security Policy
```typescript
// Before injecting HTML into Obsidian views
function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
```

## Resources
- [Obsidian Plugin Guidelines](https://docs.obsidian.md/Plugins/Releasing/Plugin+guidelines)
- [Electron Security](https://www.electronjs.org/docs/latest/tutorial/security)
