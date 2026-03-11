# Evernote Webhooks & Events - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Webhook Endpoint

```javascript
// routes/webhooks.js
const express = require('express');
const crypto = require('crypto');
const router = express.Router();

// Evernote webhook endpoint
router.get('/webhooks/evernote', (req, res) => {
  // Evernote sends GET requests for webhooks
  const {
    userId,      // Evernote user ID
    guid,        // GUID of changed note (if applicable)
    notebookGuid,// GUID of changed notebook (if applicable)
    reason       // Reason for notification
  } = req.query;

  console.log('Webhook received:', {
    userId,
    guid,
    notebookGuid,
    reason,
    timestamp: new Date().toISOString()
  });

  // Acknowledge receipt immediately
  res.status(200).send('OK');

  // Process asynchronously
  processWebhook(userId, guid, notebookGuid, reason)
    .catch(err => console.error('Webhook processing error:', err));
});

async function processWebhook(userId, guid, notebookGuid, reason) {
  // Queue the sync job
  await syncQueue.add('sync-user', {
    userId,
    guid,
    notebookGuid,
    reason,
    receivedAt: Date.now()
  });
}

module.exports = router;
```

### Step 2: Webhook Reasons

```javascript
// Evernote webhook reasons
const WebhookReasons = {
  CREATE: 'create',    // New note created
  UPDATE: 'update',    // Note updated
  // Note: No DELETE reason - must detect via sync
};

// Handle different webhook types
async function handleWebhookByReason(userId, guid, reason) {
  switch (reason) {
    case WebhookReasons.CREATE:
      await handleNoteCreated(userId, guid);
      break;

    case WebhookReasons.UPDATE:
      await handleNoteUpdated(userId, guid);
      break;

    default:
      // Unknown reason - perform full sync check
      await performIncrementalSync(userId);
  }
}
```

### Step 3: Sync State Management

```javascript
// services/sync-service.js
const Evernote = require('evernote');

class SyncService {
  constructor(noteStore) {
    this.noteStore = noteStore;
    this.lastUpdateCount = 0;
  }

  /**
   * Get current sync state
   */
  async getSyncState() {
    return this.noteStore.getSyncState();
  }

  /**
   * Check if sync is needed
   */
  async needsSync(lastKnownUpdateCount) {
    const state = await this.getSyncState();
    return state.updateCount > lastKnownUpdateCount;
  }

  /**
   * Perform incremental sync
   */
  async incrementalSync(afterUpdateCount) {
    const chunks = [];
    let currentUpdateCount = afterUpdateCount;

    while (true) {
      // Get sync chunk
      const chunk = await this.noteStore.getFilteredSyncChunk(
        currentUpdateCount,
        100, // Max entries per chunk
        {
          includeNotes: true,
          includeNotebooks: true,
          includeTags: true,
          includeExpunged: true  // Detect deletions
        }
      );

      chunks.push(chunk);

      // Check if more chunks
      if (chunk.chunkHighUSN >= chunk.updateCount) {
        break;
      }

      currentUpdateCount = chunk.chunkHighUSN;
    }

    return this.processChunks(chunks);
  }

  /**
   * Process sync chunks
   */
  processChunks(chunks) {
    const changes = {
      notes: { created: [], updated: [], deleted: [] },
      notebooks: { created: [], updated: [], deleted: [] },
      tags: { created: [], updated: [], deleted: [] }
    };

    for (const chunk of chunks) {
      // Process notes
      if (chunk.notes) {
        for (const note of chunk.notes) {
          if (note.deleted) {
            changes.notes.deleted.push(note.guid);
          } else if (note.created === note.updated) {
            changes.notes.created.push(note);
          } else {
            changes.notes.updated.push(note);
          }
        }
      }

      // Process expunged (permanently deleted)
      if (chunk.expungedNotes) {
        changes.notes.deleted.push(...chunk.expungedNotes);
      }

      // Process notebooks
      if (chunk.notebooks) {
        for (const notebook of chunk.notebooks) {
          changes.notebooks.updated.push(notebook);
        }
      }

      if (chunk.expungedNotebooks) {
        changes.notebooks.deleted.push(...chunk.expungedNotebooks);
      }

      // Process tags
      if (chunk.tags) {
        for (const tag of chunk.tags) {
          changes.tags.updated.push(tag);
        }
      }

      if (chunk.expungedTags) {
        changes.tags.deleted.push(...chunk.expungedTags);
      }
    }

    return changes;
  }
}

module.exports = SyncService;
```

### Step 4: Webhook Event Processing

```javascript
// services/event-processor.js
const EventEmitter = require('events');

class EvernoteEventProcessor extends EventEmitter {
  constructor(syncService, options = {}) {
    super();
    this.syncService = syncService;
    this.processingLock = new Map();
    this.debounceMs = options.debounceMs || 5000;
    this.pendingWebhooks = new Map();
  }

  /**
   * Handle incoming webhook (debounced)
   */
  async handleWebhook(userId, guid, reason) {
    const key = `${userId}`;

    // Debounce multiple webhooks for same user
    if (this.pendingWebhooks.has(key)) {
      clearTimeout(this.pendingWebhooks.get(key));
    }

    this.pendingWebhooks.set(key, setTimeout(async () => {
      this.pendingWebhooks.delete(key);
      await this.processUserChanges(userId);
    }, this.debounceMs));
  }

  /**
   * Process changes for a user
   */
  async processUserChanges(userId) {
    // Prevent concurrent processing
    if (this.processingLock.has(userId)) {
      console.log(`Already processing for user ${userId}`);
      return;
    }

    this.processingLock.set(userId, true);

    try {
      // Get last known update count
      const lastUpdateCount = await this.getStoredUpdateCount(userId);

      // Check if sync needed
      if (!await this.syncService.needsSync(lastUpdateCount)) {
        console.log(`No changes for user ${userId}`);
        return;
      }

      // Perform incremental sync
      const changes = await this.syncService.incrementalSync(lastUpdateCount);

      // Emit events for changes
      this.emitChangeEvents(userId, changes);

      // Store new update count
      const state = await this.syncService.getSyncState();
      await this.storeUpdateCount(userId, state.updateCount);

    } finally {
      this.processingLock.delete(userId);
    }
  }

  /**
   * Emit events for detected changes
   */
  emitChangeEvents(userId, changes) {
    // Note events
    for (const note of changes.notes.created) {
      this.emit('note:created', { userId, note });
    }

    for (const note of changes.notes.updated) {
      this.emit('note:updated', { userId, note });
    }

    for (const guid of changes.notes.deleted) {
      this.emit('note:deleted', { userId, guid });
    }

    // Notebook events
    for (const notebook of changes.notebooks.updated) {
      this.emit('notebook:updated', { userId, notebook });
    }

    for (const guid of changes.notebooks.deleted) {
      this.emit('notebook:deleted', { userId, guid });
    }

    // Tag events
    for (const tag of changes.tags.updated) {
      this.emit('tag:updated', { userId, tag });
    }

    for (const guid of changes.tags.deleted) {
      this.emit('tag:deleted', { userId, guid });
    }

    // Summary event
    this.emit('sync:complete', {
      userId,
      summary: {
        notesCreated: changes.notes.created.length,
        notesUpdated: changes.notes.updated.length,
        notesDeleted: changes.notes.deleted.length
      }
    });
  }

  // Storage methods (implement with your database)
  async getStoredUpdateCount(userId) {
    // Return stored update count for user
    return 0; // Default to 0 for initial sync
  }

  async storeUpdateCount(userId, updateCount) {
    // Store update count for user
  }
}

module.exports = EvernoteEventProcessor;
```

### Step 5: Event Handlers

```javascript
// handlers/event-handlers.js
const processor = require('./event-processor');

// Handle new notes
processor.on('note:created', async ({ userId, note }) => {
  console.log(`New note created: ${note.title}`);

  // Example: Index for search
  await searchIndex.indexNote(note);

  // Example: Send notification
  await notifications.send(userId, {
    type: 'note_created',
    title: note.title
  });
});

// Handle note updates
processor.on('note:updated', async ({ userId, note }) => {
  console.log(`Note updated: ${note.title}`);

  // Example: Update search index
  await searchIndex.updateNote(note);

  // Example: Sync to external service
  await externalSync.updateNote(userId, note);
});

// Handle note deletions
processor.on('note:deleted', async ({ userId, guid }) => {
  console.log(`Note deleted: ${guid}`);

  // Example: Remove from search index
  await searchIndex.removeNote(guid);

  // Example: Clean up related data
  await database.cleanupNoteData(guid);
});

// Handle sync completion
processor.on('sync:complete', ({ userId, summary }) => {
  console.log(`Sync complete for user ${userId}:`, summary);

  // Example: Log metrics
  metrics.recordSync({
    userId,
    ...summary
  });
});
```

### Step 6: Webhook Registration

```javascript
// Note: Webhook registration is done through Evernote Developer Portal
// API key settings, not through the API itself.

// Webhook configuration in Evernote Developer Portal:
// 1. Go to https://dev.evernote.com/
// 2. Navigate to your API key settings
// 3. Enable webhooks
// 4. Set webhook URL: https://your-domain.com/webhooks/evernote

// For local development, use ngrok:
// ngrok http 3000
// Then update webhook URL temporarily in developer portal
```

### Step 7: Polling Fallback

```javascript
// services/polling-service.js

/**
 * Fallback polling for when webhooks aren't available
 * or as a backup sync mechanism
 */
class PollingService {
  constructor(syncService, options = {}) {
    this.syncService = syncService;
    this.pollInterval = options.pollInterval || 5 * 60 * 1000; // 5 minutes
    this.users = new Map(); // userId -> lastUpdateCount
    this.timer = null;
  }

  /**
   * Start polling for a user
   */
  addUser(userId, accessToken) {
    this.users.set(userId, {
      accessToken,
      lastUpdateCount: 0
    });
  }

  /**
   * Remove user from polling
   */
  removeUser(userId) {
    this.users.delete(userId);
  }

  /**
   * Start polling loop
   */
  start() {
    if (this.timer) return;

    this.timer = setInterval(async () => {
      await this.pollAllUsers();
    }, this.pollInterval);

    console.log(`Polling started (interval: ${this.pollInterval}ms)`);
  }

  /**
   * Stop polling
   */
  stop() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  /**
   * Poll all registered users
   */
  async pollAllUsers() {
    for (const [userId, data] of this.users) {
      try {
        await this.pollUser(userId, data);
      } catch (error) {
        console.error(`Poll failed for user ${userId}:`, error.message);
      }
    }
  }

  /**
   * Poll single user for changes
   */
  async pollUser(userId, data) {
    const state = await this.syncService.getSyncState();

    if (state.updateCount > data.lastUpdateCount) {
      console.log(`Changes detected for user ${userId}`);

      const changes = await this.syncService.incrementalSync(
        data.lastUpdateCount
      );

      // Update stored count
      data.lastUpdateCount = state.updateCount;

      // Process changes
      await this.processChanges(userId, changes);
    }
  }

  async processChanges(userId, changes) {
    // Same processing as webhook handler
  }
}

module.exports = PollingService;
```


## How Evernote Webhooks Work

Unlike most APIs, Evernote webhooks only notify that a user's account changed. They do NOT include the actual changes in the payload. You must:

1. Receive webhook notification
2. Use sync API to fetch actual changes
3. Process the retrieved changes


## Webhook vs Polling

| Aspect | Webhooks | Polling |
|--------|----------|---------|
| Latency | Near real-time | Poll interval |
| Rate limit impact | None | Uses API quota |
| Reliability | Depends on network | Consistent |
| Setup complexity | Requires public URL | Simple |
| Recommended | Production | Development/backup |
