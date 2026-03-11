# Evernote Performance Tuning - Implementation Guide

> Full implementation details for the parent SKILL.md.

## Detailed Instructions

### Step 1: Response Caching

```javascript
// services/cache-service.js
const Redis = require('ioredis');

class EvernoteCacheService {
  constructor(redisUrl) {
    this.redis = new Redis(redisUrl);
    this.defaultTTL = 300; // 5 minutes
  }

  /**
   * Cache key generators
   */
  keys = {
    notebooks: (userId) => `evernote:${userId}:notebooks`,
    tags: (userId) => `evernote:${userId}:tags`,
    note: (guid) => `evernote:note:${guid}`,
    noteMetadata: (guid) => `evernote:note:${guid}:meta`,
    search: (userId, query) => `evernote:${userId}:search:${this.hashQuery(query)}`,
    syncState: (userId) => `evernote:${userId}:syncState`
  };

  hashQuery(query) {
    const crypto = require('crypto');
    return crypto.createHash('md5').update(query).digest('hex');
  }

  /**
   * Cache notebooks (longer TTL - rarely change)
   */
  async cacheNotebooks(userId, notebooks) {
    const key = this.keys.notebooks(userId);
    await this.redis.setex(key, 3600, JSON.stringify(notebooks)); // 1 hour
  }

  async getNotebooks(userId) {
    const key = this.keys.notebooks(userId);
    const cached = await this.redis.get(key);
    return cached ? JSON.parse(cached) : null;
  }

  /**
   * Cache note metadata (shorter TTL)
   */
  async cacheNoteMetadata(guid, metadata) {
    const key = this.keys.noteMetadata(guid);
    await this.redis.setex(key, this.defaultTTL, JSON.stringify(metadata));
  }

  async getNoteMetadata(guid) {
    const key = this.keys.noteMetadata(guid);
    const cached = await this.redis.get(key);
    return cached ? JSON.parse(cached) : null;
  }

  /**
   * Cache full note content (configurable TTL)
   */
  async cacheNote(guid, note, ttl = 300) {
    const key = this.keys.note(guid);
    await this.redis.setex(key, ttl, JSON.stringify(note));
  }

  async getNote(guid) {
    const key = this.keys.note(guid);
    const cached = await this.redis.get(key);
    return cached ? JSON.parse(cached) : null;
  }

  /**
   * Cache search results (short TTL)
   */
  async cacheSearch(userId, query, results) {
    const key = this.keys.search(userId, query);
    await this.redis.setex(key, 60, JSON.stringify(results)); // 1 minute
  }

  async getSearch(userId, query) {
    const key = this.keys.search(userId, query);
    const cached = await this.redis.get(key);
    return cached ? JSON.parse(cached) : null;
  }

  /**
   * Invalidate cache on changes
   */
  async invalidateNote(guid) {
    await this.redis.del(this.keys.note(guid));
    await this.redis.del(this.keys.noteMetadata(guid));
  }

  async invalidateUserCache(userId) {
    const pattern = `evernote:${userId}:*`;
    const keys = await this.redis.keys(pattern);
    if (keys.length > 0) {
      await this.redis.del(...keys);
    }
  }
}

module.exports = EvernoteCacheService;
```

### Step 2: Cached Client Wrapper

```javascript
// services/cached-evernote-client.js
const Evernote = require('evernote');
const EvernoteCacheService = require('./cache-service');

class CachedEvernoteClient {
  constructor(accessToken, userId, cacheService) {
    this.client = new Evernote.Client({
      token: accessToken,
      sandbox: process.env.EVERNOTE_SANDBOX === 'true'
    });
    this.noteStore = this.client.getNoteStore();
    this.userId = userId;
    this.cache = cacheService;
  }

  /**
   * List notebooks with caching
   */
  async listNotebooks(forceRefresh = false) {
    if (!forceRefresh) {
      const cached = await this.cache.getNotebooks(this.userId);
      if (cached) {
        console.log('Cache HIT: notebooks');
        return cached;
      }
    }

    console.log('Cache MISS: notebooks');
    const notebooks = await this.noteStore.listNotebooks();
    await this.cache.cacheNotebooks(this.userId, notebooks);
    return notebooks;
  }

  /**
   * Get note with caching
   */
  async getNote(guid, options = {}) {
    const {
      withContent = true,
      withResources = false,
      forceRefresh = false
    } = options;

    // Only cache if requesting content without resources
    const canCache = withContent && !withResources;

    if (canCache && !forceRefresh) {
      const cached = await this.cache.getNote(guid);
      if (cached) {
        console.log('Cache HIT: note', guid);
        return cached;
      }
    }

    console.log('Cache MISS: note', guid);
    const note = await this.noteStore.getNote(
      guid,
      withContent,
      withResources,
      false,
      false
    );

    if (canCache) {
      await this.cache.cacheNote(guid, note);
    }

    return note;
  }

  /**
   * Search with caching
   */
  async search(query, options = {}) {
    const { maxResults = 50, forceRefresh = false } = options;

    if (!forceRefresh) {
      const cached = await this.cache.getSearch(this.userId, query);
      if (cached) {
        console.log('Cache HIT: search', query);
        return cached;
      }
    }

    console.log('Cache MISS: search', query);
    const filter = new Evernote.NoteStore.NoteFilter({ words: query });
    const spec = new Evernote.NoteStore.NotesMetadataResultSpec({
      includeTitle: true,
      includeCreated: true,
      includeUpdated: true,
      includeTagGuids: true,
      includeNotebookGuid: true
    });

    const results = await this.noteStore.findNotesMetadata(
      filter,
      0,
      maxResults,
      spec
    );

    await this.cache.cacheSearch(this.userId, query, results);
    return results;
  }
}

module.exports = CachedEvernoteClient;
```

### Step 3: Request Batching

```javascript
// utils/request-batcher.js

class RequestBatcher {
  constructor(options = {}) {
    this.batchSize = options.batchSize || 10;
    this.batchDelay = options.batchDelay || 100;
    this.queue = [];
    this.processing = false;
  }

  /**
   * Add request to batch
   */
  async add(operation) {
    return new Promise((resolve, reject) => {
      this.queue.push({ operation, resolve, reject });

      if (!this.processing) {
        this.processBatch();
      }
    });
  }

  /**
   * Process queued requests
   */
  async processBatch() {
    if (this.queue.length === 0) {
      this.processing = false;
      return;
    }

    this.processing = true;

    // Take batch from queue
    const batch = this.queue.splice(0, this.batchSize);

    // Execute in parallel
    await Promise.all(
      batch.map(async ({ operation, resolve, reject }) => {
        try {
          const result = await operation();
          resolve(result);
        } catch (error) {
          reject(error);
        }
      })
    );

    // Small delay before next batch
    if (this.queue.length > 0) {
      await new Promise(r => setTimeout(r, this.batchDelay));
      this.processBatch();
    } else {
      this.processing = false;
    }
  }
}

module.exports = RequestBatcher;
```

### Step 4: Efficient Data Retrieval

```javascript
// services/optimized-note-service.js

class OptimizedNoteService {
  constructor(noteStore, cache) {
    this.noteStore = noteStore;
    this.cache = cache;
  }

  /**
   * Get minimal data needed (don't over-fetch)
   */
  async getNotePreview(guid) {
    // Only get metadata, not full content
    return this.noteStore.getNote(guid, false, false, false, false);
  }

  /**
   * Get notes with content in single request
   */
  async getNotesWithContent(guids) {
    // Evernote doesn't support batch note retrieval
    // Optimize by parallelizing with rate limit awareness
    const results = [];
    const batchSize = 5;

    for (let i = 0; i < guids.length; i += batchSize) {
      const batch = guids.slice(i, i + batchSize);
      const batchResults = await Promise.all(
        batch.map(guid =>
          this.noteStore.getNote(guid, true, false, false, false)
        )
      );
      results.push(...batchResults);

      // Small delay between batches
      if (i + batchSize < guids.length) {
        await new Promise(r => setTimeout(r, 100));
      }
    }

    return results;
  }

  /**
   * Get resources separately (more efficient for large files)
   */
  async getNoteWithLazyResources(guid) {
    // Get note without resource data
    const note = await this.noteStore.getNote(guid, true, false, false, false);

    // Create lazy loader for resources
    note.loadResource = async (resourceGuid) => {
      return this.noteStore.getResource(
        resourceGuid,
        true,  // withData
        false, // withRecognition
        false, // withAttributes
        false  // withAlternateData
      );
    };

    return note;
  }

  /**
   * Efficient search with pagination
   */
  async* searchPaginated(query, pageSize = 50) {
    const filter = new Evernote.NoteStore.NoteFilter({ words: query });
    const spec = new Evernote.NoteStore.NotesMetadataResultSpec({
      includeTitle: true,
      includeUpdated: true
    });

    let offset = 0;
    let total = null;

    while (total === null || offset < total) {
      const result = await this.noteStore.findNotesMetadata(
        filter,
        offset,
        pageSize,
        spec
      );

      total = result.totalNotes;

      for (const note of result.notes) {
        yield note;
      }

      offset += result.notes.length;
    }
  }
}

module.exports = OptimizedNoteService;
```

### Step 5: Connection Optimization

```javascript
// utils/connection-manager.js

class ConnectionManager {
  constructor() {
    this.clients = new Map();
    this.maxIdleTime = 5 * 60 * 1000; // 5 minutes
  }

  /**
   * Get or create client for user
   */
  getClient(userId, accessToken) {
    const existing = this.clients.get(userId);

    if (existing) {
      existing.lastUsed = Date.now();
      return existing.client;
    }

    const client = new Evernote.Client({
      token: accessToken,
      sandbox: process.env.EVERNOTE_SANDBOX === 'true'
    });

    this.clients.set(userId, {
      client,
      lastUsed: Date.now()
    });

    return client;
  }

  /**
   * Clean up idle connections
   */
  cleanup() {
    const now = Date.now();

    for (const [userId, data] of this.clients) {
      if (now - data.lastUsed > this.maxIdleTime) {
        this.clients.delete(userId);
        console.log(`Cleaned up idle connection for user ${userId}`);
      }
    }
  }

  /**
   * Start cleanup interval
   */
  startCleanup(interval = 60000) {
    setInterval(() => this.cleanup(), interval);
  }
}

module.exports = ConnectionManager;
```

### Step 6: Performance Monitoring

```javascript
// utils/performance-monitor.js

class PerformanceMonitor {
  constructor() {
    this.metrics = {
      apiCalls: 0,
      cacheHits: 0,
      cacheMisses: 0,
      totalLatency: 0,
      errors: 0
    };
    this.callDurations = [];
  }

  /**
   * Track API call
   */
  trackCall(operation, duration, fromCache = false) {
    this.metrics.apiCalls++;
    this.metrics.totalLatency += duration;
    this.callDurations.push({ operation, duration, fromCache, timestamp: Date.now() });

    if (fromCache) {
      this.metrics.cacheHits++;
    } else {
      this.metrics.cacheMisses++;
    }

    // Keep last 1000 calls
    if (this.callDurations.length > 1000) {
      this.callDurations.shift();
    }
  }

  /**
   * Track error
   */
  trackError(operation, error) {
    this.metrics.errors++;
    console.error(`[PERF] Error in ${operation}:`, error.message);
  }

  /**
   * Get performance stats
   */
  getStats() {
    const avgLatency = this.metrics.apiCalls > 0
      ? this.metrics.totalLatency / this.metrics.apiCalls
      : 0;

    const cacheHitRate = this.metrics.apiCalls > 0
      ? (this.metrics.cacheHits / this.metrics.apiCalls) * 100
      : 0;

    // Calculate p95 latency
    const sortedDurations = [...this.callDurations]
      .map(c => c.duration)
      .sort((a, b) => a - b);
    const p95Index = Math.floor(sortedDurations.length * 0.95);
    const p95Latency = sortedDurations[p95Index] || 0;

    return {
      totalCalls: this.metrics.apiCalls,
      cacheHits: this.metrics.cacheHits,
      cacheMisses: this.metrics.cacheMisses,
      cacheHitRate: `${cacheHitRate.toFixed(1)}%`,
      avgLatencyMs: avgLatency.toFixed(2),
      p95LatencyMs: p95Latency.toFixed(2),
      errors: this.metrics.errors
    };
  }

  /**
   * Create instrumented wrapper
   */
  instrument(noteStore) {
    const monitor = this;

    return new Proxy(noteStore, {
      get(target, prop) {
        const original = target[prop];

        if (typeof original !== 'function') {
          return original;
        }

        return async (...args) => {
          const start = Date.now();

          try {
            const result = await original.apply(target, args);
            const duration = Date.now() - start;
            monitor.trackCall(prop, duration);
            return result;
          } catch (error) {
            const duration = Date.now() - start;
            monitor.trackCall(prop, duration);
            monitor.trackError(prop, error);
            throw error;
          }
        };
      }
    });
  }
}

module.exports = PerformanceMonitor;
```

### Step 7: Usage Example

```javascript
// example-optimized.js
const Redis = require('ioredis');
const EvernoteCacheService = require('./services/cache-service');
const CachedEvernoteClient = require('./services/cached-evernote-client');
const PerformanceMonitor = require('./utils/performance-monitor');

async function main() {
  const redis = new Redis(process.env.REDIS_URL);
  const cache = new EvernoteCacheService(redis);
  const monitor = new PerformanceMonitor();

  const userId = 'user-123';
  const client = new CachedEvernoteClient(
    process.env.EVERNOTE_ACCESS_TOKEN,
    userId,
    cache
  );

  // Instrument for monitoring
  client.noteStore = monitor.instrument(client.noteStore);

  // First call - cache miss
  console.log('\nFirst request (cache miss):');
  console.time('First notebooks call');
  await client.listNotebooks();
  console.timeEnd('First notebooks call');

  // Second call - cache hit
  console.log('\nSecond request (cache hit):');
  console.time('Second notebooks call');
  await client.listNotebooks();
  console.timeEnd('Second notebooks call');

  // Search with caching
  console.log('\nSearch (cache miss):');
  console.time('First search');
  await client.search('meeting notes');
  console.timeEnd('First search');

  console.log('\nSearch (cache hit):');
  console.time('Second search');
  await client.search('meeting notes');
  console.timeEnd('Second search');

  // Print stats
  console.log('\nPerformance Stats:', monitor.getStats());

  redis.quit();
}

main().catch(console.error);
```


## Performance Tips

| Optimization | Impact | When to Use |
|--------------|--------|-------------|
| Cache notebooks | High | Always (rarely change) |
| Cache search results | Medium | Repeated searches |
| Lazy load resources | High | Large attachments |
| Request batching | Medium | Bulk operations |
| Skip content flag | High | Listing notes |
