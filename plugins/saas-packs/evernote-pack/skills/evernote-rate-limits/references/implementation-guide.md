# Evernote Rate Limits - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Rate Limit Handler

```javascript
// utils/rate-limiter.js

class RateLimitHandler {
  constructor(options = {}) {
    this.maxRetries = options.maxRetries || 3;
    this.onRateLimit = options.onRateLimit || (() => {});
    this.requestQueue = [];
    this.isProcessing = false;
    this.minDelay = options.minDelay || 100; // ms between requests
  }

  /**
   * Execute operation with rate limit handling
   */
  async execute(operation) {
    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        if (this.isRateLimitError(error)) {
          const waitTime = error.rateLimitDuration * 1000;

          this.onRateLimit({
            attempt: attempt + 1,
            waitTime,
            willRetry: attempt < this.maxRetries - 1
          });

          if (attempt < this.maxRetries - 1) {
            console.log(`Rate limited. Waiting ${error.rateLimitDuration}s...`);
            await this.sleep(waitTime);
            continue;
          }
        }
        throw error;
      }
    }
  }

  /**
   * Queue operations to prevent bursts
   */
  async enqueue(operation) {
    return new Promise((resolve, reject) => {
      this.requestQueue.push({ operation, resolve, reject });
      this.processQueue();
    });
  }

  async processQueue() {
    if (this.isProcessing || this.requestQueue.length === 0) {
      return;
    }

    this.isProcessing = true;

    while (this.requestQueue.length > 0) {
      const { operation, resolve, reject } = this.requestQueue.shift();

      try {
        const result = await this.execute(operation);
        resolve(result);
      } catch (error) {
        reject(error);
      }

      // Minimum delay between requests
      if (this.requestQueue.length > 0) {
        await this.sleep(this.minDelay);
      }
    }

    this.isProcessing = false;
  }

  isRateLimitError(error) {
    return error.errorCode === 19 && error.rateLimitDuration !== undefined;
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

module.exports = RateLimitHandler;
```

### Step 2: Rate-Limited Client Wrapper

```javascript
// services/rate-limited-client.js
const Evernote = require('evernote');
const RateLimitHandler = require('../utils/rate-limiter');

class RateLimitedEvernoteClient {
  constructor(accessToken, options = {}) {
    this.client = new Evernote.Client({
      token: accessToken,
      sandbox: options.sandbox || false
    });

    this.rateLimiter = new RateLimitHandler({
      maxRetries: options.maxRetries || 3,
      minDelay: options.minDelay || 100,
      onRateLimit: (info) => {
        console.log(`[Rate Limit] Attempt ${info.attempt}, wait ${info.waitTime}ms`);
        if (options.onRateLimit) {
          options.onRateLimit(info);
        }
      }
    });

    this._noteStore = null;
  }

  get noteStore() {
    if (!this._noteStore) {
      const originalStore = this.client.getNoteStore();
      this._noteStore = this.wrapWithRateLimiting(originalStore);
    }
    return this._noteStore;
  }

  wrapWithRateLimiting(store) {
    const rateLimiter = this.rateLimiter;

    return new Proxy(store, {
      get(target, prop) {
        const original = target[prop];

        if (typeof original !== 'function') {
          return original;
        }

        return (...args) => {
          return rateLimiter.enqueue(() => original.apply(target, args));
        };
      }
    });
  }
}

module.exports = RateLimitedEvernoteClient;
```

### Step 3: Batch Operations with Rate Limiting

```javascript
// utils/batch-processor.js

class BatchProcessor {
  constructor(rateLimiter, options = {}) {
    this.rateLimiter = rateLimiter;
    this.batchSize = options.batchSize || 10;
    this.delayBetweenBatches = options.delayBetweenBatches || 1000;
    this.onProgress = options.onProgress || (() => {});
  }

  /**
   * Process items in rate-limited batches
   */
  async processBatch(items, operation) {
    const results = [];
    const total = items.length;
    let processed = 0;

    // Split into batches
    const batches = this.chunkArray(items, this.batchSize);

    for (const batch of batches) {
      const batchResults = await Promise.all(
        batch.map(item =>
          this.rateLimiter.enqueue(async () => {
            try {
              const result = await operation(item);
              return { success: true, item, result };
            } catch (error) {
              return { success: false, item, error: error.message };
            }
          })
        )
      );

      results.push(...batchResults);
      processed += batch.length;

      this.onProgress({
        processed,
        total,
        percentage: Math.round((processed / total) * 100)
      });

      // Delay between batches
      if (processed < total) {
        await this.sleep(this.delayBetweenBatches);
      }
    }

    return {
      total: results.length,
      successful: results.filter(r => r.success).length,
      failed: results.filter(r => !r.success).length,
      results
    };
  }

  chunkArray(array, size) {
    const chunks = [];
    for (let i = 0; i < array.length; i += size) {
      chunks.push(array.slice(i, i + size));
    }
    return chunks;
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

module.exports = BatchProcessor;
```

### Step 4: Avoiding Rate Limits

```javascript
// Best practices to minimize rate limit hits

class EvernoteOptimizer {
  constructor(noteStore) {
    this.noteStore = noteStore;
    this.notebookCache = null;
    this.tagCache = null;
    this.cacheExpiry = 5 * 60 * 1000; // 5 minutes
  }

  /**
   * BAD: Multiple calls for same data
   */
  async badPattern() {
    const notebooks = await this.noteStore.listNotebooks(); // Call 1
    const notebooks2 = await this.noteStore.listNotebooks(); // Call 2 (wasteful)
  }

  /**
   * GOOD: Cache frequently accessed data
   */
  async getNotebooks(forceRefresh = false) {
    if (!forceRefresh && this.notebookCache && Date.now() < this.notebookCacheExpiry) {
      return this.notebookCache;
    }

    this.notebookCache = await this.noteStore.listNotebooks();
    this.notebookCacheExpiry = Date.now() + this.cacheExpiry;
    return this.notebookCache;
  }

  /**
   * BAD: Getting full note when only metadata needed
   */
  async badGetNote(guid) {
    return this.noteStore.getNote(guid, true, true, true, true); // All data
  }

  /**
   * GOOD: Only request what you need
   */
  async efficientGetNote(guid, options = {}) {
    return this.noteStore.getNote(
      guid,
      options.withContent || false,
      options.withResources || false,
      options.withRecognition || false,
      options.withAlternateData || false
    );
  }

  /**
   * BAD: Polling for changes
   */
  async badPolling() {
    while (true) {
      const state = await this.noteStore.getSyncState();
      await sleep(1000); // Constant polling = rate limit suicide
    }
  }

  /**
   * GOOD: Use webhooks + intelligent sync
   */
  async intelligentSync(lastUpdateCount) {
    const state = await this.noteStore.getSyncState();

    if (state.updateCount === lastUpdateCount) {
      return { hasChanges: false };
    }

    // Only sync if changes detected
    const chunks = await this.noteStore.getFilteredSyncChunk(
      lastUpdateCount,
      100,
      {
        includeNotes: true,
        includeNotebooks: true,
        includeTags: true
      }
    );

    return {
      hasChanges: true,
      updateCount: state.updateCount,
      chunks
    };
  }

  /**
   * BAD: Getting resources individually
   */
  async badResourceFetch(noteGuid) {
    const note = await this.noteStore.getNote(noteGuid, true, false, false, false);
    // Then making separate calls for each resource
    for (const resource of note.resources || []) {
      await this.noteStore.getResource(resource.guid, true, false, false, false);
    }
  }

  /**
   * GOOD: Get resources with note
   */
  async efficientResourceFetch(noteGuid) {
    return this.noteStore.getNote(
      noteGuid,
      true,  // withContent
      true,  // withResourcesData - get all resources in one call
      false, // withResourcesRecognition
      false  // withResourcesAlternateData
    );
  }
}
```

### Step 5: Rate Limit Monitoring

```javascript
// utils/rate-monitor.js

class RateLimitMonitor {
  constructor() {
    this.history = [];
    this.windowSize = 60 * 60 * 1000; // 1 hour
  }

  recordRequest() {
    const now = Date.now();
    this.history.push(now);
    this.pruneOldEntries(now);
  }

  recordRateLimit(rateLimitDuration) {
    this.history.push({
      timestamp: Date.now(),
      rateLimited: true,
      duration: rateLimitDuration
    });
  }

  pruneOldEntries(now) {
    const cutoff = now - this.windowSize;
    this.history = this.history.filter(entry => {
      const timestamp = typeof entry === 'number' ? entry : entry.timestamp;
      return timestamp > cutoff;
    });
  }

  getStats() {
    const now = Date.now();
    this.pruneOldEntries(now);

    const requests = this.history.filter(e => typeof e === 'number');
    const rateLimits = this.history.filter(e => e.rateLimited);

    return {
      requestsInLastHour: requests.length,
      rateLimitsHit: rateLimits.length,
      averageRequestsPerMinute: (requests.length / 60).toFixed(2),
      lastRateLimit: rateLimits.length > 0 ?
        new Date(rateLimits[rateLimits.length - 1].timestamp) : null
    };
  }

  shouldThrottle() {
    const stats = this.getStats();
    // Conservative threshold - throttle if approaching limits
    return stats.requestsInLastHour > 500 || stats.rateLimitsHit > 0;
  }
}

module.exports = RateLimitMonitor;
```

### Step 6: Usage Example

```javascript
// example.js
const RateLimitedEvernoteClient = require('./services/rate-limited-client');
const BatchProcessor = require('./utils/batch-processor');
const RateLimitMonitor = require('./utils/rate-monitor');

async function main() {
  const monitor = new RateLimitMonitor();

  const client = new RateLimitedEvernoteClient(
    process.env.EVERNOTE_ACCESS_TOKEN,
    {
      sandbox: true,
      maxRetries: 3,
      minDelay: 200,
      onRateLimit: (info) => {
        monitor.recordRateLimit(info.waitTime / 1000);
        console.log('Rate limit stats:', monitor.getStats());
      }
    }
  );

  const noteStore = client.noteStore;

  // All operations are automatically rate-limited
  const notebooks = await noteStore.listNotebooks();
  console.log('Notebooks:', notebooks.length);

  // Batch process with progress
  const processor = new BatchProcessor(client.rateLimiter, {
    batchSize: 5,
    delayBetweenBatches: 500,
    onProgress: (progress) => {
      console.log(`Progress: ${progress.percentage}%`);
    }
  });

  // Example: Process multiple notes
  const noteGuids = ['guid1', 'guid2', 'guid3'];
  const results = await processor.processBatch(
    noteGuids,
    guid => noteStore.getNote(guid, false, false, false, false)
  );

  console.log('Batch results:', results);
  console.log('Final stats:', monitor.getStats());
}

main().catch(console.error);
```


## Rate Limit Structure

| Scope | Limit Window | Error |
|-------|--------------|-------|
| Per API key | 1 hour | EDAMSystemException |
| Per user | 1 hour | EDAMSystemException |
| Combined | Per key + per user | RATE_LIMIT_REACHED |

**Key points:**
- Limits are NOT publicly documented (intentionally)
- Hitting the limit returns `rateLimitDuration` (seconds to wait)
- Limits are generally generous for normal usage
- Initial sync boost available (24 hours, must be requested)


## Best Practices Summary

| Do | Don't |
|----|-------|
| Cache frequently accessed data | Make duplicate API calls |
| Request only needed data | Use withResourcesData when not needed |
| Use webhooks for change detection | Poll getSyncState repeatedly |
| Batch operations with delays | Fire many requests simultaneously |
| Handle rateLimitDuration | Retry immediately after rate limit |
