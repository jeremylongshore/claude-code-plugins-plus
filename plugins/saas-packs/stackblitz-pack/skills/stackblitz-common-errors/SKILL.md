---
name: stackblitz-common-errors
description: |
  Fix WebContainer and StackBlitz errors: COOP/COEP, SharedArrayBuffer, boot failures.
  Use when WebContainers fail to boot, embeds don't load,
  or processes crash inside WebContainers.
  Trigger: "stackblitz error", "webcontainer error", "SharedArrayBuffer not defined".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ide, webcontainers, stackblitz]
compatible-with: claude-code
---

# StackBlitz Common Errors

## Error Reference

### SharedArrayBuffer is not defined
**Cause:** Missing cross-origin isolation headers.
```
Cross-Origin-Embedder-Policy: require-corp
Cross-Origin-Opener-Policy: same-origin
```
**Fix:** Add both headers to your server. In Vite: `server.headers` config.

### Failed to boot WebContainer
**Cause:** Only one WebContainer instance allowed per page.
```typescript
// BAD: Multiple boot calls
const wc1 = await WebContainer.boot();
const wc2 = await WebContainer.boot(); // Fails!

// GOOD: Singleton pattern
let instance: WebContainer | null = null;
async function getWC() {
  if (!instance) instance = await WebContainer.boot();
  return instance;
}
```

### npm install hangs or fails
**Cause:** Large dependency tree or network issue in WebContainer.
```typescript
// Use --prefer-offline and minimal deps
const proc = await wc.spawn('npm', ['install', '--prefer-offline']);
const code = await proc.exit;
if (code !== 0) {
  console.error('Install failed, retrying...');
  const retry = await wc.spawn('npm', ['install']);
  await retry.exit;
}
```

### server-ready event never fires
**Cause:** Application not listening on a port.
```typescript
// Ensure your app calls listen()
// app.listen(3000) -- required for server-ready event
// Also check process exit code for crashes
wc.on('error', (err) => console.error('WC error:', err));
```

### File operations fail with ENOENT
**Cause:** Parent directory doesn't exist.
```typescript
// Create parent directories first
await wc.fs.mkdir('/src/components', { recursive: true });
await wc.fs.writeFile('/src/components/Button.tsx', content);
```

## Quick Diagnostic

```typescript
// Check WebContainer state
async function diagnose(wc: WebContainer) {
  try {
    await wc.fs.readdir('/');
    console.log('FS: OK');
  } catch { console.error('FS: FAILED'); }

  try {
    const proc = await wc.spawn('node', ['-v']);
    await proc.exit;
    console.log('Node: OK');
  } catch { console.error('Node: FAILED'); }
}
```

## Error Handling

| Error | Retryable | Action |
|-------|-----------|--------|
| Missing COOP/COEP | No | Fix server headers |
| Multiple boot | No | Use singleton pattern |
| npm install fail | Yes | Retry once, then report |
| ENOENT | No | Create parent dirs |
| Process crash | Yes | Restart process |

## Resources

- [WebContainer API Reference](https://webcontainers.io/api)
- [Browser Compatibility](https://webcontainers.io/guides/browser-support)

## Next Steps

For debugging, see `stackblitz-debug-bundle`.
