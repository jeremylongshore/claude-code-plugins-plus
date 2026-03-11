# Evernote Reference Architecture - Implementation Guide

> Full implementation details for the parent SKILL.md.


## Architecture Patterns

### Pattern 1: Basic Integration

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Client    │────>│  Your API    │────>│  Evernote API   │
│   (Web/App) │<────│  Server      │<────│                 │
└─────────────┘     └──────────────┘     └─────────────────┘
                           │
                    ┌──────┴──────┐
                    │  Database   │
                    │  (Tokens)   │
                    └─────────────┘
```

**Use when:**
- Small user base (<1000)
- Simple CRUD operations
- Low API call volume

### Pattern 2: Cached Integration

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Client    │────>│  Your API    │────>│  Evernote API   │
│             │<────│  Server      │<────│                 │
└─────────────┘     └──────┬───────┘     └─────────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────┴─────┐ ┌────┴────┐ ┌─────┴─────┐
        │   Redis   │ │ Database│ │   CDN     │
        │  (Cache)  │ │ (Tokens)│ │ (Static)  │
        └───────────┘ └─────────┘ └───────────┘
```

**Key components:**
- Redis for API response caching
- CDN for static content (note images)
- Database for token storage

### Pattern 3: Event-Driven Architecture

```
                                    ┌─────────────────┐
                                    │  Evernote API   │
                                    └────────┬────────┘
                                             │
┌──────────┐    ┌──────────────┐    ┌────────┴────────┐
│ Webhook  │───>│ Event Queue  │───>│ Sync Workers    │
│ Receiver │    │ (SQS/Pub-Sub)│    │ (Lambda/Cloud   │
└──────────┘    └──────────────┘    │  Functions)     │
                                    └────────┬────────┘
                                             │
                      ┌──────────────────────┴──────────────────────┐
                      │                      │                      │
               ┌──────┴──────┐       ┌───────┴───────┐     ┌───────┴───────┐
               │  Search     │       │   Database    │     │  Analytics    │
               │  Index      │       │   (Notes)     │     │  (BigQuery)   │
               └─────────────┘       └───────────────┘     └───────────────┘
```

**Use when:**
- Real-time sync required
- Multiple downstream consumers
- High reliability needed

### Pattern 4: Full Production Architecture

```
                                         ┌─────────────────────────────┐
                                         │       Evernote Cloud        │
                                         │  ┌─────────┐  ┌─────────┐   │
                                         │  │ User    │  │ Note    │   │
                                         │  │ Store   │  │ Store   │   │
                                         │  └─────────┘  └─────────┘   │
                                         └──────────┬──────────────────┘
                                                    │
┌────────────────────────────────────────────────────────────────────────┐
│                            Your Infrastructure                          │
│                                                                        │
│   ┌──────────────┐        ┌──────────────────┐                        │
│   │   CloudFlare │        │   API Gateway    │                        │
│   │   (WAF/CDN)  │───────>│   (Rate Limit)   │                        │
│   └──────────────┘        └────────┬─────────┘                        │
│                                    │                                   │
│         ┌──────────────────────────┼──────────────────────────┐       │
│         │                          │                          │       │
│   ┌─────┴─────┐            ┌───────┴───────┐          ┌──────┴──────┐ │
│   │  OAuth    │            │   Core API    │          │  Webhook    │ │
│   │  Service  │            │   Service     │          │  Service    │ │
│   └─────┬─────┘            └───────┬───────┘          └──────┬──────┘ │
│         │                          │                          │       │
│   ┌─────┴─────────────────────────┴──────────────────────────┴─────┐  │
│   │                        Message Bus (Kafka/SNS)                  │  │
│   └─────────────────────────────────┬──────────────────────────────┘  │
│                                     │                                  │
│         ┌──────────────────────────┬┴──────────────────────────┐      │
│         │                          │                          │       │
│   ┌─────┴─────┐            ┌───────┴───────┐          ┌──────┴──────┐ │
│   │  Sync     │            │   Search      │          │ Analytics   │ │
│   │  Worker   │            │   Service     │          │ Pipeline    │ │
│   └─────┬─────┘            └───────┬───────┘          └──────┬──────┘ │
│         │                          │                          │       │
│   ┌─────┴─────────────────────────┴──────────────────────────┴─────┐  │
│   │                        Data Layer                               │  │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐           │  │
│   │  │PostgreSQL│ │ Redis   │  │Elastic- │  │BigQuery │           │  │
│   │  │(Primary) │ │(Cache)  │  │search   │  │(OLAP)   │           │  │
│   │  └─────────┘  └─────────┘  └─────────┘  └─────────┘           │  │
│   └────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```


## Component Details

### API Gateway Layer

```javascript
// config/api-gateway.js
module.exports = {
  // Rate limiting per user
  rateLimit: {
    windowMs: 60 * 1000, // 1 minute
    max: 100, // 100 requests per minute
    keyGenerator: (req) => req.user?.id || req.ip
  },

  // Request timeout
  timeout: 30000,

  // Circuit breaker for Evernote API
  circuitBreaker: {
    failureThreshold: 5,
    resetTimeout: 60000
  },

  // Retry configuration
  retry: {
    maxRetries: 3,
    baseDelay: 1000,
    maxDelay: 10000
  }
};
```

### Core API Service

```javascript
// services/core-api/index.js
const express = require('express');
const { EvernoteClient } = require('./evernote-client');
const { CacheService } = require('./cache');
const { EventBus } = require('./events');

class CoreAPIService {
  constructor(config) {
    this.cache = new CacheService(config.redis);
    this.events = new EventBus(config.kafka);
  }

  async getNote(userId, noteGuid) {
    // Try cache first
    const cacheKey = `note:${noteGuid}`;
    const cached = await this.cache.get(cacheKey);
    if (cached) return cached;

    // Fetch from Evernote
    const client = await this.getClientForUser(userId);
    const note = await client.noteStore.getNote(
      noteGuid, true, false, false, false
    );

    // Cache and return
    await this.cache.set(cacheKey, note, 300);
    return note;
  }

  async createNote(userId, noteData) {
    const client = await this.getClientForUser(userId);
    const note = await client.noteStore.createNote(noteData);

    // Emit event for downstream services
    await this.events.emit('note.created', {
      userId,
      noteGuid: note.guid,
      timestamp: Date.now()
    });

    return note;
  }
}
```

### Sync Worker

```javascript
// workers/sync-worker/index.js
const { SyncService } = require('./sync-service');

class SyncWorker {
  constructor(config) {
    this.syncService = new SyncService(config);
    this.batchSize = 100;
  }

  async processWebhook(message) {
    const { userId } = message;

    // Get last sync state
    const lastUSN = await this.getLastSyncUSN(userId);

    // Fetch changes
    const changes = await this.syncService.getChanges(userId, lastUSN);

    // Process in batches
    for (const chunk of this.chunk(changes.notes, this.batchSize)) {
      await this.processNoteBatch(userId, chunk);
    }

    // Update sync state
    await this.updateSyncUSN(userId, changes.currentUSN);
  }

  async processNoteBatch(userId, notes) {
    const operations = notes.map(note => ({
      updateOne: {
        filter: { guid: note.guid },
        update: {
          $set: {
            userId,
            title: note.title,
            contentHash: note.contentHash,
            updated: new Date(note.updated),
            syncedAt: new Date()
          }
        },
        upsert: true
      }
    }));

    await this.db.collection('notes').bulkWrite(operations);
  }

  chunk(array, size) {
    const chunks = [];
    for (let i = 0; i < array.length; i += size) {
      chunks.push(array.slice(i, i + size));
    }
    return chunks;
  }
}
```

### Search Service

```javascript
// services/search/index.js
const { Client } = require('@elastic/elasticsearch');

class SearchService {
  constructor(config) {
    this.elastic = new Client({ node: config.elasticsearchUrl });
    this.indexName = 'evernote-notes';
  }

  async indexNote(note) {
    await this.elastic.index({
      index: this.indexName,
      id: note.guid,
      document: {
        userId: note.userId,
        title: note.title,
        content: this.extractText(note.content),
        tags: note.tags,
        notebook: note.notebookGuid,
        created: note.created,
        updated: note.updated
      }
    });
  }

  async search(userId, query, options = {}) {
    const { from = 0, size = 20 } = options;

    const result = await this.elastic.search({
      index: this.indexName,
      query: {
        bool: {
          must: [
            { term: { userId } },
            {
              multi_match: {
                query,
                fields: ['title^2', 'content', 'tags']
              }
            }
          ]
        }
      },
      from,
      size,
      highlight: {
        fields: {
          title: {},
          content: { fragment_size: 150 }
        }
      }
    });

    return {
      total: result.hits.total.value,
      hits: result.hits.hits.map(hit => ({
        guid: hit._id,
        score: hit._score,
        ...hit._source,
        highlights: hit.highlight
      }))
    };
  }

  extractText(enml) {
    return enml
      .replace(/<[^>]+>/g, ' ')
      .replace(/&\w+;/g, ' ')
      .replace(/\s+/g, ' ')
      .trim();
  }
}
```


## Database Schema

```sql
-- PostgreSQL schema

-- Users and tokens
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  evernote_user_id BIGINT UNIQUE NOT NULL,
  username VARCHAR(255),
  email VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tokens (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  access_token TEXT NOT NULL, -- Encrypted
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT tokens_user_unique UNIQUE (user_id)
);

-- Sync state
CREATE TABLE sync_state (
  user_id INTEGER PRIMARY KEY REFERENCES users(id),
  last_update_count INTEGER DEFAULT 0,
  last_sync_at TIMESTAMP,
  full_sync_required BOOLEAN DEFAULT true
);

-- Local note cache (optional)
CREATE TABLE notes_cache (
  guid UUID PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  title VARCHAR(255),
  content_hash VARCHAR(64),
  notebook_guid UUID,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  INDEX idx_notes_user (user_id),
  INDEX idx_notes_notebook (notebook_guid)
);
```


## Infrastructure as Code

```yaml

resources:
  evernote_service:
    type: aws_ecs_service
    properties:
      name: evernote-api
      cluster: production
      task_definition: evernote-api-task
      desired_count: 3
      deployment_configuration:
        maximum_percent: 200
        minimum_healthy_percent: 100

  # Redis Cache
  redis_cluster:
    type: aws_elasticache_cluster
    properties:
      cluster_id: evernote-cache
      engine: redis
      node_type: cache.t3.medium
      num_cache_nodes: 2

  # RDS PostgreSQL
  database:
    type: aws_db_instance
    properties:
      identifier: evernote-db
      engine: postgres
      engine_version: "15"
      instance_class: db.t3.medium
      allocated_storage: 100
      multi_az: true

  # SQS Queue
  webhook_queue:
    type: aws_sqs_queue
    properties:
      name: evernote-webhooks
      visibility_timeout_seconds: 300
      message_retention_seconds: 1209600
```


## Scaling Considerations

| Component | Scaling Strategy | Trigger |
|-----------|------------------|---------|
| API Servers | Horizontal (auto-scale) | CPU > 70%, Request latency > 500ms |
| Sync Workers | Queue-based | Queue depth > 1000 |
| Cache | Cluster mode | Memory > 80% |
| Database | Read replicas | Read IOPS > 5000 |
| Search | Index sharding | Documents > 10M |
