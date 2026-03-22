---
name: obsidian-security-basics
description: |
  Implement secure Obsidian plugin development practices. Covers credential
  storage, input validation, XSS prevention, network security, URI handler
  safety, and Electron security. Use when handling user data, storing API keys,
  making network requests, or preparing for community plugin submission.
  Trigger with phrases like "obsidian security", "secure obsidian plugin",
  "obsidian data protection", "obsidian privacy", "obsidian api key storage".
allowed-tools: Read, Write, Edit, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [obsidian, security, authentication, privacy, electron]

---
# Obsidian Security Basics

## Overview
Security practices for Obsidian plugin development. Plugins run with full vault filesystem access and can make arbitrary network requests inside Electron. Responsible development requires protecting credentials, sanitizing external data, validating URI handlers, minimizing permissions, and following Obsidian's plugin guidelines to avoid community submission rejection.

## Prerequisites
- Obsidian plugin development environment
- Understanding that `.obsidian/plugins/<id>/data.json` is synced by cloud services
- Awareness of [Obsidian Plugin Guidelines](https://docs.obsidian.md/Plugins/Releasing/Plugin+guidelines)

## Instructions

### Step 1: Credential Storage — Never in data.json

Plugin settings (`data.json`) live inside the vault and are synced by iCloud, Dropbox, Obsidian Sync, and Git. API keys stored here are effectively public.

```typescript
// BAD: API key stored in plugin settings (synced to cloud, committed to Git)
interface BadSettings {
  apiKey: string; // This ends up in .obsidian/plugins/my-plugin/data.json
}

// GOOD: Use Electron's safeStorage for desktop (encrypted at OS level)
import { Platform } from 'obsidian';

export class SecureStorage {
  private plugin: Plugin;

  constructor(plugin: Plugin) { this.plugin = plugin; }

  async storeSecret(key: string, value: string): Promise<void> {
    if (Platform.isDesktopApp) {
      // Electron's safeStorage uses OS keychain (Keychain on macOS, DPAPI on Windows)
      const { safeStorage } = require('electron').remote || require('@electron/remote');
      if (safeStorage.isEncryptionAvailable()) {
        const encrypted = safeStorage.encryptString(value);
        const data = await this.plugin.loadData() ?? {};
        data[`_encrypted_${key}`] = encrypted.toString('base64');
        await this.plugin.saveData(data);
        return;
      }
    }
    // Fallback for mobile or when encryption unavailable: prompt each session
    // Store only in memory — never persisted
    this.memoryStore.set(key, value);
  }

  async getSecret(key: string): Promise<string | null> {
    if (Platform.isDesktopApp) {
      const { safeStorage } = require('electron').remote || require('@electron/remote');
      const data = await this.plugin.loadData();
      const encrypted = data?.[`_encrypted_${key}`];
      if (encrypted && safeStorage.isEncryptionAvailable()) {
        return safeStorage.decryptString(Buffer.from(encrypted, 'base64'));
      }
    }
    return this.memoryStore.get(key) ?? null;
  }

  private memoryStore = new Map<string, string>();
}

// Alternative: prompt user each session (simplest, most secure)
async onload() {
  if (!this.apiKey) {
    this.apiKey = await this.promptForApiKey();
  }
}
```

### Step 2: Input Validation and XSS Prevention

Data from HTTP responses, clipboard, or URI handlers must be sanitized before rendering.

```typescript
// Sanitize HTML content before inserting into Obsidian views
function sanitizeHtml(input: string): string {
  // Strip dangerous elements
  input = input.replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '');
  input = input.replace(/<iframe[^>]*>[\s\S]*?<\/iframe>/gi, '');
  input = input.replace(/<object[^>]*>[\s\S]*?<\/object>/gi, '');
  input = input.replace(/<embed[^>]*>/gi, '');
  // Strip event handlers
  input = input.replace(/\bon\w+\s*=\s*"[^"]*"/gi, '');
  input = input.replace(/\bon\w+\s*=\s*'[^']*'/gi, '');
  // Strip javascript: URIs
  input = input.replace(/href\s*=\s*"javascript:[^"]*"/gi, 'href="#"');
  return input;
}

// For plain text in DOM elements — escape instead of strip
function escapeHtml(text: string): string {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// Safe DOM creation (preferred in Obsidian)
// Use createEl with text content — Obsidian escapes automatically
container.createEl('p', { text: userInput }); // Safe — text is escaped
container.createEl('p').innerHTML = userInput;  // DANGEROUS — raw HTML injection

// For markdown content from external sources
function sanitizeMarkdown(md: string): string {
  // Remove HTML blocks that could contain scripts
  md = md.replace(/<script[\s\S]*?<\/script>/gi, '');
  // Remove image onerror handlers
  md = md.replace(/onerror\s*=\s*["'][^"']*["']/gi, '');
  // Limit length to prevent DoS
  if (md.length > 500_000) md = md.substring(0, 500_000);
  return md;
}
```

### Step 3: Secure URI Handler Registration

Obsidian's `registerObsidianProtocolHandler` lets external apps trigger plugin actions via `obsidian://` URIs. Validate all parameters.

```typescript
this.registerObsidianProtocolHandler('myplugin', async (params) => {
  // Whitelist allowed actions
  const ALLOWED_ACTIONS = ['open', 'create', 'search'] as const;
  type Action = typeof ALLOWED_ACTIONS[number];

  const action = params.action as string;
  if (!ALLOWED_ACTIONS.includes(action as Action)) {
    new Notice(`Invalid action: ${action}`);
    return;
  }

  // Sanitize file paths — prevent directory traversal
  const path = params.path?.replace(/\.\./g, '').replace(/^\//, '');
  if (!path) {
    new Notice('Missing path parameter');
    return;
  }

  // Validate path is within vault
  const normalized = normalizePath(path);
  if (normalized.includes('..') || normalized.startsWith('/')) {
    new Notice('Invalid path');
    return;
  }

  // Limit content length
  const content = params.content?.substring(0, 100_000) ?? '';

  switch (action as Action) {
    case 'open': {
      const file = this.app.vault.getAbstractFileByPath(normalized);
      if (file instanceof TFile) {
        await this.app.workspace.getLeaf().openFile(file);
      } else {
        new Notice(`File not found: ${normalized}`);
      }
      break;
    }
    case 'create': {
      await this.app.vault.create(normalized, content);
      new Notice(`Created: ${normalized}`);
      break;
    }
    case 'search': {
      // Use Obsidian's built-in search
      (this.app as any).internalPlugins.plugins['global-search']
        ?.instance.openGlobalSearch(content);
      break;
    }
  }
});
```

### Step 4: Secure Network Requests

```typescript
import { requestUrl, RequestUrlParam } from 'obsidian';

// Always use Obsidian's requestUrl — it respects proxy settings and CORS
async function secureFetch(url: string, options?: Partial<RequestUrlParam>): Promise<any> {
  // Enforce HTTPS
  if (!url.startsWith('https://')) {
    throw new Error('Only HTTPS requests are allowed');
  }

  // Allowlist domains (prevents SSRF if URL comes from user input)
  const ALLOWED_DOMAINS = ['api.example.com', 'cdn.example.com'];
  const urlObj = new URL(url);
  if (!ALLOWED_DOMAINS.includes(urlObj.hostname)) {
    throw new Error(`Domain not allowed: ${urlObj.hostname}`);
  }

  const response = await requestUrl({
    url,
    method: 'GET',
    headers: {
      'User-Agent': 'ObsidianPlugin/1.0',
      ...options?.headers,
    },
    ...options,
  });

  if (response.status < 200 || response.status >= 300) {
    throw new Error(`HTTP ${response.status}: ${url}`);
  }

  return response.json;
}

// Never log or display full API responses — they may contain PII
function redactForLogging(data: any): any {
  const redacted = { ...data };
  const sensitiveKeys = ['apiKey', 'token', 'password', 'secret', 'authorization'];
  for (const key of Object.keys(redacted)) {
    if (sensitiveKeys.some(s => key.toLowerCase().includes(s))) {
      redacted[key] = '[REDACTED]';
    }
  }
  return redacted;
}
```

### Step 5: Permission Minimization

```typescript
// manifest.json — only set isDesktopOnly if you actually need Electron APIs
{
  "isDesktopOnly": false
  // Obsidian has no granular permission model in manifest.json.
  // The review team evaluates your code for:
  // - Network requests: must be essential to plugin function
  // - Filesystem access outside vault: strongly discouraged
  // - No telemetry/analytics without explicit user consent
  // - No remote code loading (eval, new Function, loading JS from URL)
}

// At runtime: guard platform-specific code
import { Platform, FileSystemAdapter } from 'obsidian';

function getVaultBasePath(): string | null {
  if (this.app.vault.adapter instanceof FileSystemAdapter) {
    return this.app.vault.adapter.getBasePath();
    // IMPORTANT: never access files outside this basePath
  }
  return null; // Mobile — no filesystem access outside vault
}

// Guard Electron APIs
if (Platform.isDesktopApp) {
  // Safe to use: require('electron'), child_process, etc.
} else {
  // Mobile: these APIs don't exist — provide fallback or disable feature
}
```

### Step 6: Plugin Review Rejection Checklist

Obsidian's plugin review team will reject plugins for these violations:

```typescript
// REJECTED: eval() or dynamic code execution
eval(userInput);                    // Never
new Function('return ' + code)();  // Never
document.createElement('script');  // Never for external scripts

// REJECTED: remote code loading
const script = document.createElement('script');
script.src = 'https://cdn.example.com/lib.js';  // Load at build time instead

// REJECTED: console.log in production
console.log('user data:', settings);  // Remove before submission

// REJECTED: unencrypted credential storage
this.saveData({ apiKey: 'sk-abc123' });  // Use SecureStorage (Step 1)

// REJECTED: undisclosed network requests
fetch('https://analytics.example.com/track', { body: ... });  // No hidden telemetry

// APPROVED alternatives:
// - Bundle dependencies with esbuild (no runtime loading)
// - Use a debug flag for console statements
// - Document all network requests in README
// - Get explicit consent before any data leaves the device
```

## Output
- SecureStorage class using Electron's safeStorage for encrypted credential storage
- HTML and markdown sanitization for all external content
- URI handler with action whitelist and path validation
- Secure network request wrapper with HTTPS enforcement and domain allowlist
- Platform-specific guards for desktop/mobile code paths
- Plugin review rejection checklist with approved alternatives

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| API key synced to cloud | Stored in `data.json` | Use `SecureStorage` with Electron `safeStorage` |
| XSS in note preview | Unsanitized external HTML | Use `createEl` with `text` property, or `sanitizeHtml` |
| Directory traversal via URI | Unvalidated path parameter | Strip `..`, normalize, validate within vault |
| SSRF from user-provided URL | No domain allowlist | Validate against ALLOWED_DOMAINS before `requestUrl` |
| Plugin rejected on review | `eval`, `console.log`, or telemetry | Follow rejection checklist (Step 6) |
| `safeStorage` unavailable | Older Electron version or mobile | Fall back to per-session prompt |

## Examples

### Content Security for Custom Views
```typescript
// When rendering external content in an ItemView
async onOpen() {
  const externalData = await this.fetchData();
  const container = this.containerEl.children[1];
  container.empty();

  // Safe: text content is escaped by createEl
  container.createEl('h3', { text: externalData.title });
  container.createEl('p', { text: externalData.summary });

  // If you must render HTML, sanitize first
  const safeHtml = sanitizeHtml(externalData.htmlContent);
  const htmlContainer = container.createEl('div');
  htmlContainer.innerHTML = safeHtml;
}
```

### Audit Your Plugin for Security Issues
```bash
# Quick security audit of plugin source code
grep -rn 'eval(\|new Function(' src/ --include="*.ts" && echo "FAIL: dynamic code execution"
grep -rn 'innerHTML\s*=' src/ --include="*.ts" && echo "WARN: check for XSS"
grep -rn 'console\.log' src/ --include="*.ts" | grep -v '// DEBUG' && echo "WARN: console.log in prod"
grep -rn 'apiKey\|secret\|password' src/ --include="*.ts" && echo "CHECK: credential handling"
echo "Done."
```

## Resources
- [Obsidian Plugin Guidelines](https://docs.obsidian.md/Plugins/Releasing/Plugin+guidelines)
- [Electron Security](https://www.electronjs.org/docs/latest/tutorial/security)
- [OWASP XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [Obsidian requestUrl API](https://docs.obsidian.md/Reference/TypeScript+API/requestUrl)

## Next Steps
For production readiness checks, see `obsidian-prod-checklist`.
For deployment and community submission, see `obsidian-deploy-integration`.
