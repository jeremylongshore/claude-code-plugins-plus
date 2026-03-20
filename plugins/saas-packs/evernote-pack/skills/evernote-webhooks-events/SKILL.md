---
name: evernote-webhooks-events
description: |
  Implement Evernote webhook notifications and sync events.
  Use when handling note changes, implementing real-time sync,
  or processing Evernote notifications.
  Trigger with phrases like "evernote webhook", "evernote events",
  "evernote sync", "evernote notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Webhooks & Events

## Overview
Implement Evernote webhook notifications for real-time change detection. Evernote webhooks notify your endpoint that changes occurred, but you must use the sync API to retrieve the actual changed data.

## Prerequisites
- Evernote API key with webhook permissions
- HTTPS endpoint accessible from the internet
- Understanding of Evernote sync API

## Instructions

### Step 1: Webhook Endpoint

Create an Express endpoint that receives webhook POST requests. Evernote sends `userId`, `guid` (notebook GUID), and `reason` (create, update, notebook) as query parameters. Respond with HTTP 200 immediately, then process asynchronously.

```javascript
app.post('/evernote/webhook', (req, res) => {
  const { userId, guid, reason } = req.query;
  res.sendStatus(200); // Respond immediately

  // Process asynchronously
  processWebhook({ userId, notebookGuid: guid, reason })
    .catch(err => console.error('Webhook processing failed:', err));
});
```

### Step 2: Webhook Reasons

Handle three webhook reasons: `create` (new note created), `update` (note modified), and `notebook` (notebook-level change). Each triggers a sync of the affected notebook.

### Step 3: Sync State Management

Store the last sync USN per user. On webhook receipt, call `getSyncState()` to get the current server USN, then `getFilteredSyncChunk()` to fetch only the changes since your last sync.

```javascript
const syncState = await noteStore.getSyncState();
const chunk = await noteStore.getFilteredSyncChunk(
  lastUSN,
  100,  // maxEntries
  new Evernote.NoteStore.SyncChunkFilter({
    includeNotes: true,
    includeNotebooks: true,
    includeTags: true
  })
);
```

### Step 4: Event Processing and Handlers

Route sync chunk entries to typed handlers: `onNoteCreated`, `onNoteUpdated`, `onNoteDeleted`, `onNotebookChanged`. Implement idempotency by tracking processed USNs to handle duplicate webhook deliveries.

### Step 5: Polling Fallback

Implement a polling fallback for environments where webhooks are unavailable. Poll `getSyncState()` on a timer (e.g., every 5 minutes) and sync when `updateCount` changes.

For the full webhook server, sync manager, event handlers, and polling implementations, see [Implementation Guide](references/implementation-guide.md).

## Output
- Express webhook endpoint with async processing
- Sync state manager with USN tracking
- Event router for create, update, and delete operations
- Idempotent event processing (handles duplicate deliveries)
- Polling fallback for non-webhook environments

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook not received | URL not reachable from Evernote servers | Verify HTTPS endpoint is publicly accessible |
| Duplicate webhooks | Network retries by Evernote | Track processed USNs for idempotency |
| Missing changes | Race condition between webhook and sync | Re-sync with small delay after webhook |
| Sync timeout | Large change set in chunk | Reduce `maxEntries` per chunk, paginate |

## Resources
- [Webhooks Overview](https://dev.evernote.com/doc/articles/webhooks.php)
- [Synchronization](https://dev.evernote.com/doc/articles/synchronization.php)
- [Developer Portal](https://dev.evernote.com/)

## Next Steps
For performance optimization, see `evernote-performance-tuning`.

## Examples

**Real-time note sync**: Receive webhook on note update, fetch the sync chunk, update local database, and notify connected clients via WebSocket.

**Polling-based sync**: For environments behind firewalls, poll `getSyncState()` every 5 minutes and process any changes via the same handler pipeline used by webhooks.
