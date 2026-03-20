---
name: evernote-debug-bundle
description: |
  Debug Evernote API issues with diagnostic tools and techniques.
  Use when troubleshooting API calls, inspecting requests/responses,
  or diagnosing integration problems.
  Trigger with phrases like "debug evernote", "evernote diagnostic",
  "troubleshoot evernote", "evernote logs", "inspect evernote".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`

## Overview
Comprehensive debugging toolkit for Evernote API integrations, including request/response logging, ENML validation with auto-fix, token inspection, and diagnostic CLI utilities.

## Prerequisites
- Evernote SDK installed
- Node.js environment
- Understanding of common Evernote errors (see `evernote-common-errors`)

## Instructions

### Step 1: Debug Logger

Create a logger that captures API method names, arguments (with token redaction), response times, and error details. Write to both console and file for post-mortem analysis.

```javascript
class EvernoteDebugLogger {
  constructor(logFile = 'evernote-debug.log') {
    this.logFile = logFile;
    this.requests = [];
  }

  logRequest(method, args, response, duration, error) {
    const entry = {
      timestamp: new Date().toISOString(),
      method,
      duration: `${duration}ms`,
      success: !error,
      error: error?.message || error?.errorCode
    };
    this.requests.push(entry);
    fs.appendFileSync(this.logFile, JSON.stringify(entry) + '\n');
  }
}
```

### Step 2: Instrumented Client Wrapper

Wrap the NoteStore with a Proxy that automatically logs every API call, measures response time, and catches errors. This adds zero-config debugging to any existing integration.

```javascript
function instrumentNoteStore(noteStore, logger) {
  return new Proxy(noteStore, {
    get(target, prop) {
      if (typeof target[prop] !== 'function') return target[prop];
      return async (...args) => {
        const start = Date.now();
        try {
          const result = await target[prop](...args);
          logger.logRequest(prop, args, result, Date.now() - start);
          return result;
        } catch (error) {
          logger.logRequest(prop, args, null, Date.now() - start, error);
          throw error;
        }
      };
    }
  });
}
```

### Step 3: ENML Validator

Validate ENML content against the DTD rules: check for XML declaration, DOCTYPE, `<en-note>` root, forbidden elements, and unclosed tags. Optionally auto-fix common issues (add missing headers, close tags, strip forbidden elements).

### Step 4: Token Inspector

Check token validity by calling `userStore.getUser()`. Report token owner, expiration date (`edam_expires`), account type, and remaining upload quota.

### Step 5: Diagnostic CLI

Create a CLI script with commands: `diagnose` (run all checks), `validate-enml <file>` (validate ENML content), `inspect-token` (show token info), `test-api` (verify API connectivity).

For the full debug logger, instrumented client, ENML auto-fixer, token inspector, and diagnostic CLI, see [Implementation Guide](references/implementation-guide.md).

## Output
- `EvernoteDebugLogger` with file and console output
- Proxy-based instrumented NoteStore wrapper
- ENML validator with auto-fix capability
- Token and account inspector utility
- Diagnostic CLI with `diagnose`, `validate-enml`, `inspect-token` commands

## Error Handling
| Issue | Diagnostic | Solution |
|-------|------------|----------|
| Auth failures | Run `inspect-token` to check expiration | Re-authenticate if expired |
| ENML errors | Run `validate-enml` on content | Auto-fix or manually correct |
| Rate limits | Check request frequency in debug log | Increase delay between calls |
| Missing data | Inspect response in debug log | Verify API parameters (withContent flags) |

## Resources
- [Error Handling](https://dev.evernote.com/doc/articles/error_handling.php)
- [ENML DTD](http://xml.evernote.com/pub/enml2.dtd)
- [API Reference](https://dev.evernote.com/doc/reference/)

## Next Steps
For rate limit handling, see `evernote-rate-limits`.

## Examples

**Request tracing**: Wrap NoteStore with the instrumented proxy, run your workflow, then review `evernote-debug.log` for slow calls (>2s), failed requests, and rate limit hits.

**ENML debugging**: Pipe note content through the ENML validator to find missing DOCTYPE, forbidden `<script>` tags, or unclosed elements. Use auto-fix mode to correct issues automatically.
