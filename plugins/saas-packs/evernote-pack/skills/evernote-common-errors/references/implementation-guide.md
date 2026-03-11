# Evernote Common Errors - Implementation Guide

> Full implementation details for the parent SKILL.md.


## Error Types

Evernote uses three main exception types:

| Exception | When Thrown |
|-----------|-------------|
| `EDAMUserException` | Client error - invalid input, permissions |
| `EDAMSystemException` | Server error - rate limits, maintenance |
| `EDAMNotFoundException` | Resource not found - invalid GUID |


## EDAMUserException Errors

### BAD_DATA_FORMAT

**Cause:** Invalid ENML content or malformed data

```javascript
// Error
{
  errorCode: 1, // BAD_DATA_FORMAT
  parameter: 'Note.content'
}

// Common causes and fixes:

// 1. Missing XML declaration
// Wrong:
'<en-note><p>Hello</p></en-note>'

// Correct:
`<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">
<en-note><p>Hello</p></en-note>`

// 2. Forbidden HTML elements
// Wrong: contains <script>
`<en-note><script>alert('hi')</script></en-note>`

// Correct: remove scripts
`<en-note><p>Content only</p></en-note>`

// 3. Unclosed tags
// Wrong:
'<en-note><p>Hello<br></en-note>'

// Correct:
'<en-note><p>Hello</p><br/></en-note>'
```

**Fix:** Validate ENML before sending:

```javascript
function validateENML(content) {
  const errors = [];

  // Required declarations
  if (!content.includes('<?xml version="1.0"')) {
    errors.push('Missing XML declaration');
  }
  if (!content.includes('<!DOCTYPE en-note')) {
    errors.push('Missing DOCTYPE');
  }
  if (!content.includes('<en-note>')) {
    errors.push('Missing <en-note> root element');
  }

  // Forbidden elements
  const forbidden = [
    /<script/i, /<form/i, /<input/i, /<button/i,
    /<iframe/i, /<object/i, /<embed/i, /<applet/i
  ];

  forbidden.forEach(pattern => {
    if (pattern.test(content)) {
      errors.push(`Forbidden element: ${pattern.source}`);
    }
  });

  // Forbidden attributes
  if (/\s(class|id|onclick|onload|onerror)=/i.test(content)) {
    errors.push('Forbidden attributes (class, id, event handlers)');
  }

  return { valid: errors.length === 0, errors };
}
```

### DATA_REQUIRED

**Cause:** Missing required field

```javascript
// Error
{
  errorCode: 2, // DATA_REQUIRED
  parameter: 'Note.title'
}

// Fix: Ensure required fields are set
const note = new Evernote.Types.Note();
note.title = 'Required Title';  // Cannot be null or empty
note.content = validENMLContent; // Cannot be null
```

### PERMISSION_DENIED

**Cause:** API key lacks required permissions

```javascript
// Error
{
  errorCode: 3, // PERMISSION_DENIED
  parameter: 'NoteStore.shareNote'
}

// Causes:
// 1. API key doesn't have sharing permission
// 2. Trying to access business features without business API key
// 3. Accessing notes in shared notebooks without permission

// Fix: Request appropriate permissions when creating API key
// See: https://dev.evernote.com/doc/articles/permissions.php
```

### INVALID_AUTH

**Cause:** Invalid or expired authentication token

```javascript
// Error
{
  errorCode: 4, // INVALID_AUTH
  parameter: 'authenticationToken'
}

// Fix: Check token validity
async function checkTokenValidity(client) {
  try {
    const userStore = client.getUserStore();
    await userStore.getUser();
    return { valid: true };
  } catch (error) {
    if (error.errorCode === 4) {
      return {
        valid: false,
        reason: 'Token expired or revoked',
        action: 'Re-authenticate via OAuth'
      };
    }
    throw error;
  }
}
```

### AUTH_EXPIRED

**Cause:** Token has passed expiration date

```javascript
// Error
{
  errorCode: 5, // AUTH_EXPIRED
  parameter: 'authenticationToken'
}

// Tokens expire after 1 year by default
// Users can set shorter: 1 day, 1 week, 1 month

// Fix: Store and check expiration
function isTokenExpired(expirationTimestamp) {
  return Date.now() > expirationTimestamp;
}

// When authenticating, save edam_expires:
// results.edam_expires contains expiration timestamp
```

### LIMIT_REACHED

**Cause:** Account limits exceeded

```javascript
// Error
{
  errorCode: 6, // LIMIT_REACHED
  parameter: 'Notebook.name'
}

// Account limits:
// - 250 notebooks max
// - 100,000 tags max
// - 100,000 notes max (business accounts)
// - Upload limits per month

// Fix: Check limits before creating
async function canCreateNotebook(noteStore) {
  const notebooks = await noteStore.listNotebooks();
  return notebooks.length < 250;
}
```

### QUOTA_REACHED

**Cause:** Monthly upload quota exceeded

```javascript
// Error
{
  errorCode: 7, // QUOTA_REACHED
  parameter: 'Note.content'
}

// Quotas vary by account type:
// - Basic: 60 MB/month
// - Premium: 10 GB/month
// - Business: 20 GB/month (per user)

// Check remaining quota
async function getRemainingQuota(userStore) {
  const user = await userStore.getUser();
  const accounting = user.accounting;

  return {
    uploadLimit: accounting.uploadLimit,
    uploadLimitEnd: new Date(accounting.uploadLimitEnd),
    uploaded: accounting.uploaded,
    remaining: accounting.uploadLimit - accounting.uploaded
  };
}
```


## EDAMSystemException Errors

### RATE_LIMIT_REACHED

**Cause:** Too many API calls per hour

```javascript
// Error
{
  errorCode: 19, // RATE_LIMIT_REACHED
  rateLimitDuration: 300 // seconds until reset
}

// Fix: Implement exponential backoff
async function withRateLimitRetry(operation, maxRetries = 3) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      if (error.errorCode === 19 && error.rateLimitDuration) {
        console.log(`Rate limited. Waiting ${error.rateLimitDuration}s...`);
        await sleep(error.rateLimitDuration * 1000);
        continue;
      }
      throw error;
    }
  }
  throw new Error('Max retries exceeded');
}

const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
```

### SYSTEM_MAINTENANCE

**Cause:** Evernote service is under maintenance

```javascript
// Error
{
  errorCode: 1, // UNKNOWN (with message about maintenance)
  message: 'Service temporarily unavailable'
}

// Fix: Retry with backoff
async function withMaintenanceRetry(operation) {
  const delays = [1000, 5000, 15000, 60000]; // Progressive delays

  for (const delay of delays) {
    try {
      return await operation();
    } catch (error) {
      if (error.message?.includes('temporarily unavailable')) {
        console.log(`Service maintenance. Retrying in ${delay / 1000}s...`);
        await sleep(delay);
        continue;
      }
      throw error;
    }
  }
  throw new Error('Service unavailable - maintenance ongoing');
}
```


## EDAMNotFoundException Errors

**Cause:** Referenced resource doesn't exist

```javascript
// Error
{
  identifier: 'Note.guid',
  key: '12345678-abcd-1234-efgh-invalid00000'
}

// Common scenarios:
// 1. Note was deleted
// 2. Note is in trash
// 3. Invalid GUID format
// 4. Note belongs to different user

// Fix: Handle gracefully
async function safeGetNote(noteStore, guid) {
  try {
    return await noteStore.getNote(guid, true, false, false, false);
  } catch (error) {
    if (error.identifier === 'Note.guid') {
      console.log(`Note not found: ${guid}`);
      return null;
    }
    throw error;
  }
}
```


## Error Handling Service

```javascript
// services/error-handler.js
const Evernote = require('evernote');

class EvernoteErrorHandler {
  static handle(error) {
    // EDAMUserException
    if (error.errorCode !== undefined && error.parameter !== undefined) {
      return this.handleUserException(error);
    }

    // EDAMSystemException
    if (error.errorCode !== undefined && error.rateLimitDuration !== undefined) {
      return this.handleSystemException(error);
    }

    // EDAMNotFoundException
    if (error.identifier !== undefined) {
      return this.handleNotFoundException(error);
    }

    // Unknown error
    return {
      type: 'UNKNOWN',
      message: error.message || 'Unknown Evernote error',
      recoverable: false,
      original: error
    };
  }

  static handleUserException(error) {
    const codes = {
      1: { name: 'BAD_DATA_FORMAT', action: 'Validate input data format' },
      2: { name: 'DATA_REQUIRED', action: 'Provide required field' },
      3: { name: 'PERMISSION_DENIED', action: 'Check API key permissions' },
      4: { name: 'INVALID_AUTH', action: 'Re-authenticate user' },
      5: { name: 'AUTH_EXPIRED', action: 'Token expired, re-authenticate' },
      6: { name: 'LIMIT_REACHED', action: 'Account limit exceeded' },
      7: { name: 'QUOTA_REACHED', action: 'Upload quota exceeded' }
    };

    const info = codes[error.errorCode] || { name: 'UNKNOWN', action: 'Check documentation' };

    return {
      type: 'USER_EXCEPTION',
      code: error.errorCode,
      name: info.name,
      parameter: error.parameter,
      action: info.action,
      recoverable: [4, 5].includes(error.errorCode),
      original: error
    };
  }

  static handleSystemException(error) {
    return {
      type: 'SYSTEM_EXCEPTION',
      code: error.errorCode,
      rateLimitDuration: error.rateLimitDuration,
      action: `Wait ${error.rateLimitDuration} seconds before retrying`,
      recoverable: true,
      original: error
    };
  }

  static handleNotFoundException(error) {
    return {
      type: 'NOT_FOUND',
      identifier: error.identifier,
      key: error.key,
      action: 'Resource does not exist or was deleted',
      recoverable: false,
      original: error
    };
  }
}

module.exports = EvernoteErrorHandler;
```


## Usage Example

```javascript
const ErrorHandler = require('./services/error-handler');

async function createNoteSafely(noteStore, note) {
  try {
    return await noteStore.createNote(note);
  } catch (error) {
    const handled = ErrorHandler.handle(error);

    console.error('Evernote error:', handled.name || handled.type);
    console.error('Parameter:', handled.parameter || handled.identifier);
    console.error('Action:', handled.action);

    if (handled.recoverable) {
      console.log('Error is recoverable');
      if (handled.rateLimitDuration) {
        await sleep(handled.rateLimitDuration * 1000);
        return noteStore.createNote(note);
      }
    }

    throw error;
  }
}
```


## Quick Reference

| Code | Exception | Cause | Fix |
|------|-----------|-------|-----|
| 1 | UserException | Bad data format | Validate ENML |
| 2 | UserException | Missing required field | Add required field |
| 3 | UserException | Permission denied | Check API key |
| 4 | UserException | Invalid auth | Re-authenticate |
| 5 | UserException | Auth expired | Refresh token |
| 6 | UserException | Limit reached | Check account limits |
| 7 | UserException | Quota reached | Check upload quota |
| 19 | SystemException | Rate limit | Wait rateLimitDuration |
| - | NotFoundException | GUID not found | Verify resource exists |
