---
name: evernote-common-errors
description: |
  Diagnose and fix common Evernote API errors.
  Use when encountering Evernote API exceptions, debugging failures,
  or troubleshooting integration issues.
  Trigger with phrases like "evernote error", "evernote exception",
  "fix evernote issue", "debug evernote", "evernote troubleshooting".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Common Errors

## Overview
Comprehensive guide to diagnosing and resolving Evernote API errors. Evernote uses three exception types: `EDAMUserException` (client errors), `EDAMSystemException` (server/rate limit errors), and `EDAMNotFoundException` (invalid GUIDs).

## Prerequisites
- Basic Evernote SDK setup
- Understanding of Evernote data model

## Instructions

### EDAMUserException Error Codes

| Code | Name | Cause | Fix |
|------|------|-------|-----|
| 1 | `BAD_DATA_FORMAT` | Invalid ENML, missing DOCTYPE | Validate ENML before sending; check for forbidden elements |
| 2 | `DATA_REQUIRED` | Missing required field (title, content) | Ensure `note.title` and `note.content` are set |
| 3 | `PERMISSION_DENIED` | API key lacks permissions | Request additional permissions from Evernote |
| 4 | `INVALID_AUTH` | Invalid or revoked token | Re-authenticate user via OAuth |
| 5 | `AUTH_EXPIRED` | Token past expiration date | Check `edam_expires`, refresh token |
| 6 | `LIMIT_REACHED` | Account limit exceeded (250 notebooks) | Clean up resources before creating new ones |
| 7 | `QUOTA_REACHED` | Monthly upload quota exceeded | Check `user.accounting.remaining` |

### ENML Validation

The most common error is `BAD_DATA_FORMAT` from invalid ENML. Validate before sending:

```javascript
function validateENML(content) {
  const errors = [];
  if (!content.includes('<?xml version="1.0"')) errors.push('Missing XML declaration');
  if (!content.includes('<!DOCTYPE en-note')) errors.push('Missing DOCTYPE');
  if (!content.includes('<en-note>')) errors.push('Missing <en-note> root');

  const forbidden = [/<script/i, /<form/i, /<iframe/i, /<input/i];
  forbidden.forEach(p => { if (p.test(content)) errors.push(`Forbidden: ${p.source}`); });

  if (/\s(class|id|onclick)=/i.test(content)) errors.push('Forbidden attributes');
  return { valid: errors.length === 0, errors };
}
```

### EDAMSystemException Handling

Rate limit errors include `rateLimitDuration` (seconds to wait). Maintenance errors should be retried with progressive backoff.

```javascript
async function withRetry(operation, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation();
    } catch (error) {
      if (error.rateLimitDuration) {
        await new Promise(r => setTimeout(r, error.rateLimitDuration * 1000));
        continue;
      }
      throw error;
    }
  }
}
```

### EDAMNotFoundException Handling

Thrown when a GUID does not exist (deleted note, wrong user, invalid format). Handle gracefully by returning null instead of throwing.

```javascript
async function safeGetNote(noteStore, guid) {
  try {
    return await noteStore.getNote(guid, true, false, false, false);
  } catch (error) {
    if (error.identifier === 'Note.guid') return null;
    throw error;
  }
}
```

### Error Handler Service

Build a centralized error handler that classifies exceptions and returns structured results with `type`, `code`, `action`, and `recoverable` flags. See [Implementation Guide](references/implementation-guide.md) for the complete `EvernoteErrorHandler` class.

## Output
- Error code reference table for all `EDAMUserException` codes
- ENML validation utility that catches common content errors
- Rate limit retry with `rateLimitDuration` handling
- Safe getter pattern for `EDAMNotFoundException`
- Centralized `EvernoteErrorHandler` service class

## Error Handling
| Exception | When Thrown | Recovery |
|-----------|------------|----------|
| `EDAMUserException` | Client error (invalid input, permissions) | Fix input or re-authenticate |
| `EDAMSystemException` | Server error (rate limits, maintenance) | Wait and retry |
| `EDAMNotFoundException` | Resource not found (invalid GUID) | Verify GUID, check trash |

## Resources
- [Error Handling](https://dev.evernote.com/doc/articles/error_handling.php)
- [Rate Limits](https://dev.evernote.com/doc/articles/rate_limits.php)
- [API Reference](https://dev.evernote.com/doc/reference/)
- [ENML DTD](http://xml.evernote.com/pub/enml2.dtd)

## Next Steps
For debugging tools and techniques, see `evernote-debug-bundle`.

## Examples

**ENML debugging**: Note creation fails with `BAD_DATA_FORMAT`. Run `validateENML()` on the content to identify missing DOCTYPE, unclosed tags, or forbidden elements like `<script>`.

**Token refresh flow**: API call returns `AUTH_EXPIRED` (code 5). Check stored `edam_expires` timestamp, redirect user to OAuth re-authorization, store new token with updated expiration.
