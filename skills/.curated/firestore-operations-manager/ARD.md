# ARD: Firestore Operations Manager Skill

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## System Context

This skill operates within the Firestore ecosystem on Google Cloud Platform. The primary components are:

```
┌──────────────┐     ┌───────────────────┐     ┌──────────────────┐
│ Admin SDK     │────▶│ Cloud Firestore    │────▶│ Composite Indexes│
│ (Node.js)     │     │ (Document DB)      │     │ (auto + manual)  │
└──────────────┘     └───────┬───────────┘     └──────────────────┘
                              │
                    ┌─────────┴──────────┐
                    │                     │
              ┌─────▼──────┐     ┌───────▼────────┐
              │ Security    │     │ Firestore       │
              │ Rules       │     │ Emulator        │
              │ (deploy)    │     │ (localhost:8080) │
              └────────────┘     └────────────────┘
```

### External Systems

| System | Role | Interface |
|--------|------|-----------|
| Cloud Firestore | Document database, query engine | Admin SDK `firestore()`, REST API |
| Security Rules | Access control layer evaluated on every read/write | `firestore.rules` file deployed via CLI |
| Composite Indexes | Required for multi-field queries | `firestore.indexes.json` deployed via CLI |
| Firestore Emulator | Local Firestore replica for testing | `localhost:8080`, reset between test runs |
| Firebase Auth | Identity provider (rules reference `request.auth`) | Auth emulator at `localhost:9099` for testing |

## Data Flow

### Standard CRUD Flow

```
1. Identify operation type (create/read/update/delete)
2. Validate schema: read sample doc to understand existing fields
3. Check security rules: will the operation be allowed?
4. Check indexes: does the query need a composite index?
5. Execute operation (single doc or batch)
6. Verify result (read-after-write or emulator assertion)
```

### Batch Migration Flow

```
1. Read migration spec: source collection, target field(s), transform function
2. Check for existing checkpoint in _migrations/{migrationId}
3. Query next batch of documents (500, starting after checkpoint cursor)
4. Apply transform to each document
5. Commit batch (500 writes max per commit)
6. Write checkpoint: { lastDocId, processedCount, status: "in_progress" }
7. Repeat steps 3-6 until no more documents
8. Write final checkpoint: { processedCount, skippedCount, status: "completed" }
```

### Security Rules Testing Flow

```
1. Write firestore.rules with helper functions
2. Start Firestore + Auth emulators
3. Create test contexts (authenticated, unauthenticated, admin)
4. Assert each access pattern (read/write per collection per role)
5. Fix failing assertions by adjusting rules
6. Deploy: firebase deploy --only firestore:rules
```

## Design Decisions

### DD-1: Batch Over Individual Writes

**Decision**: All multi-document operations use `WriteBatch` (up to 500 operations) rather than individual `doc.set()` or `doc.update()` calls.

**Rationale**: Individual writes incur one round trip each. A batch of 500 writes completes in a single round trip, reducing latency by ~500x and cost by reducing billable operations. Firestore enforces a hard limit of 500 operations per batch commit.

**Implementation**: Chunk document arrays into groups of 500, commit each chunk, and log progress:

```typescript
const BATCH_SIZE = 500;
for (let i = 0; i < docs.length; i += BATCH_SIZE) {
  const batch = db.batch();
  const chunk = docs.slice(i, i + BATCH_SIZE);
  chunk.forEach(doc => batch.update(doc.ref, transform(doc.data())));
  await batch.commit();
  console.log(`Committed ${Math.min(i + BATCH_SIZE, docs.length)} / ${docs.length}`);
}
```

### DD-2: Cursor-Based Pagination for Large Reads

**Decision**: Queries that may return more than 100 documents use `startAfter(lastDoc)` cursor pagination, never `offset()`.

**Rationale**: Firestore's `offset(N)` still reads and bills for the skipped N documents. Cursor-based pagination with `startAfter()` reads only the next page, making it O(pageSize) per page instead of O(offset + pageSize).

**Trade-off**: Requires storing the last document snapshot or a deterministic sort field. All paginated queries must include an `orderBy()` clause.

### DD-3: Emulator-First Testing

**Decision**: All security rules and query patterns are tested against the Firestore emulator before any production deployment.

**Rationale**: Security rules errors in production silently block operations with `PERMISSION_DENIED`. The emulator provides instant feedback and supports `@firebase/rules-unit-testing` for programmatic assertions. Emulator tests run in < 5 seconds versus deploying rules to production (30-60 seconds).

**Constraint**: The emulator does not enforce billing or quotas, so cost estimation must be done separately.

### DD-4: Checkpoint-Based Migration Resumption

**Decision**: Long-running migrations write a checkpoint document after each batch to `_migrations/{migrationId}`.

**Rationale**: A migration processing 100,000 documents takes 200 batch commits. If the script crashes at batch 150, without checkpoints it must restart from document 0 (re-reading 75,000 already-processed documents). With checkpoints, it reads the last checkpoint and resumes from document 75,001.

**Checkpoint document schema**:

```typescript
interface MigrationCheckpoint {
  migrationId: string;
  collection: string;
  lastDocumentId: string;        // cursor for startAfter()
  processedCount: number;
  skippedCount: number;
  failedCount: number;
  status: "in_progress" | "completed" | "failed";
  startedAt: Timestamp;
  updatedAt: Timestamp;
}
```

### DD-5: Distributed Counters for Hot Documents

**Decision**: Documents expected to receive > 1 write per second use a sharded counter pattern instead of `FieldValue.increment()` on a single document.

**Rationale**: Firestore supports a sustained write rate of 1 write per second per document. Higher rates cause `ABORTED` errors due to contention. Distributing writes across N shard documents and summing on read provides Nx throughput.

**When to use**: Page view counters, like counts, real-time vote tallies. Not needed for user profile updates or low-frequency writes.

### DD-6: Index-Aware Query Generation

**Decision**: When generating a query with multiple `where()` filters or `where()` + `orderBy()` on different fields, the skill must also produce the composite index definition.

**Rationale**: Firestore requires composite indexes for these queries. Without the index, the query fails at runtime with `FAILED_PRECONDITION`. Generating the index alongside the query prevents this failure mode entirely.

## Component Design

### Migration Engine

```
MigrationRunner
├── readCheckpoint(migrationId)     → MigrationCheckpoint | null
├── runBatch(query, transform)      → { processed, skipped, failed }
├── writeCheckpoint(checkpoint)     → void
├── run(config)                     → MigrationResult
│   ├── Resume from checkpoint if exists
│   ├── Loop: query batch → transform → commit → checkpoint
│   └── Write final status
└── dryRun(config)                  → MigrationResult (reads only, no writes)
```

### Rules Generator

```
RulesGenerator
├── addCollection(name, accessPatterns)
├── addHelper(name, body)
├── addFieldValidation(collection, fieldRules)
├── generate()                       → string (firestore.rules content)
└── generateTests()                  → string (rules-unit-testing code)
```

### Index Manager

```
IndexManager
├── analyzeQuery(query)              → IndexDefinition | null
├── readExistingIndexes(path)        → IndexDefinition[]
├── mergeIndexes(existing, new)      → IndexDefinition[]
└── writeIndexFile(path, indexes)    → void
```

## Failure Modes and Recovery

| Failure | Detection | Recovery |
|---------|-----------|----------|
| PERMISSION_DENIED on write | Error code from Admin SDK | Check security rules; test with emulator; verify auth context |
| FAILED_PRECONDITION (missing index) | Error message contains index creation URL | Add index to `firestore.indexes.json`; deploy with `firebase deploy --only firestore:indexes` |
| ABORTED (write contention) | Transaction retry count > 0 | Admin SDK auto-retries 5 times; if persists, redesign to reduce writes to that document |
| Batch commit partially fails | Exception mid-batch (network, timeout) | Resume from last checkpoint; the failed batch is atomic (all or nothing) |
| DEADLINE_EXCEEDED on read | Query took > 60 seconds | Add indexes; reduce query scope with tighter filters; paginate |
| RESOURCE_EXHAUSTED | 429 from Firestore API | Back off; check if sustained write rate > 10k/sec database limit |

## Observability

### Migration Logging

Every batch commit logs:

```
[migration:backfill-status-field] Batch 150/200 committed. Processed: 75000, Skipped: 12, Failed: 0. Elapsed: 4m32s.
```

### Cost Estimation

Before executing large operations, estimate cost:

```
Operation: backfill 100,000 documents
  Reads:   100,000 × $0.06/100k = $0.06
  Writes:  100,000 × $0.18/100k = $0.18
  Total estimated cost: $0.24
```

### Key Metrics

- Batch commit latency (p50/p95 per commit)
- Documents processed per minute
- Contention retry count (should be near zero)
- Security rules evaluation latency (visible in Firebase Console > Firestore > Rules)
