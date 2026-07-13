# Firestore Operations Manager: Error Reference

## Security Rules Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `PERMISSION_DENIED: Missing or insufficient permissions` | Security rules block the read or write | Check `firestore.rules` for the matching collection path; verify `request.auth` is not null and meets rule conditions |
| `PERMISSION_DENIED` on admin SDK writes | Admin SDK bypasses rules by default; this error means the service account lacks IAM roles | Grant `roles/datastore.user` to the service account in IAM |
| Rules pass in emulator but fail in production | Rules reference a document that does not exist in production (e.g., `get()` on missing user profile) | Ensure referenced documents exist before deploying; add null checks in rules |
| `request.resource.data.X` undefined | Write operation does not include field `X` that rules validate | Add the required field to the write payload, or adjust rules to use `request.resource.data.get('X', default)` |

## Composite Index Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `FAILED_PRECONDITION: The query requires an index` | Query uses multiple `where()` clauses or `where()` + `orderBy()` on different fields without a composite index | Click the URL in the error message to auto-create, or add to `firestore.indexes.json` and deploy |
| Index build stuck at "Building" | Large collection, or conflicting index on same fields | Wait (can take hours for millions of docs); check Firebase Console > Firestore > Indexes for status |
| `INVALID_ARGUMENT: Too many composite indexes` | Exceeded 200 composite index limit per database | Remove unused indexes; consolidate queries to share indexes |
| Query works locally but fails in production | Emulator does not enforce index requirements | Always deploy indexes before deploying code that uses new queries |

## Write Contention Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ABORTED: Too much contention on these documents` | Multiple clients writing to the same document simultaneously (> 1 write/sec sustained) | Use distributed counters or sharded writes for high-frequency update paths |
| `ABORTED` inside `runTransaction()` | Transaction read-set modified by another write before commit | Admin SDK auto-retries up to 5 times; if still failing, reduce transaction scope or redesign data model |
| Transaction succeeds on retry but data looks wrong | Read outside transaction sees stale data; write based on stale read | Move all reads that inform writes inside `runTransaction()` |

## Batch Operation Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `INVALID_ARGUMENT: maximum 500 writes allowed per request` | Batch contains > 500 operations | Chunk operations into groups of 500; commit each chunk separately |
| `DEADLINE_EXCEEDED` on `batch.commit()` | Batch took > 270 seconds server-side | Reduce batch size; check if individual document writes trigger expensive Cloud Functions |
| Partial failure on batch | Network error after server received but before client got response | Batch commits are atomic: either all 500 succeed or none do; safe to retry the entire batch |
| `NOT_FOUND: No document to update` inside batch | `batch.update()` called on a document that does not exist | Use `batch.set(ref, data, { merge: true })` instead, or verify document existence before batching |

## Transaction Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `ABORTED: Transaction was aborted due to contention` | Concurrent writes to documents in the transaction's read set | Reduce documents read in transaction; Admin SDK retries automatically |
| `DEADLINE_EXCEEDED: Transaction has expired` | Transaction exceeded 270-second server-side limit | Break large transactions into smaller ones; avoid long-running async work inside transaction |
| `INVALID_ARGUMENT: Transaction has already been committed/rolled back` | Calling operations on a transaction object after it resolved | Ensure all operations happen before the transaction callback returns |
| Writes outside transaction not seeing transaction results | Reads after `runTransaction()` returns may hit cache | Use `{ source: 'server' }` for critical post-transaction reads on client SDK |

## Query Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `INVALID_ARGUMENT: Cannot have inequality filters on multiple properties` | Query has `where('a', '>', x)` and `where('b', '<', y)` | Restructure query: inequality filter on one field only; use composite index for second field with `==` |
| `INVALID_ARGUMENT: Order by must match the first inequality field` | `orderBy('name')` when inequality filter is on `createdAt` | Add `orderBy('createdAt')` before any other `orderBy()` |
| Empty results when documents exist | Query field name has typo, or field stored as different type (string vs number) | Verify field name casing; check document in Firebase Console; Firestore is case-sensitive |
| `RESOURCE_EXHAUSTED: Quota exceeded` | Exceeded read quota (50k reads/minute on free tier) | Upgrade to Blaze plan; optimize queries with tighter filters and limits |

## Emulator Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `EADDRINUSE: address already in use :::8080` | Another process (or previous emulator) using port 8080 | Kill the process: `lsof -ti:8080 \| xargs kill`; or change port in `firebase.json` |
| `Error: Could not start Firestore Emulator, port taken` | Same as above but reported by Firebase CLI | Stop other emulator instances; check for zombie Java processes |
| Emulator data disappears between restarts | Emulator does not persist by default | Use `--export-on-exit=./emulator-data` and `--import=./emulator-data` flags |
| Rules changes not reflected in emulator | Emulator loaded rules at startup | Restart emulator after rules changes; or use hot-reload (CLI v13+) |
| `connect ECONNREFUSED 127.0.0.1:8080` | Emulator not running or wrong port | Start emulator: `firebase emulators:start --only firestore`; verify port matches code |

## Data Migration Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Migration script re-processes already-migrated documents | No checkpoint mechanism; script restarted from beginning | Implement checkpoint pattern: write `_migrations/{id}` doc after each batch with `lastDocumentId` |
| Documents have mixed old/new schema | Migration interrupted midway | Resume from checkpoint; run validation query to find documents missing the new field |
| `INVALID_ARGUMENT: Value for argument "data" is not a valid Firestore document` | Transform function returned undefined or invalid type | Validate transform output before writing; skip documents that produce invalid results |
| Migration too slow (hours for 100k docs) | Processing documents one at a time instead of in batches | Use batch writes (500 per commit); parallelize with multiple query cursors on sharded key |

## Cost and Billing Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Unexpected high Firestore bill | Runaway query without `.limit()`; or real-time listener on large collection | Add `.limit()` to all queries; audit listeners; check Firebase Console > Usage |
| `RESOURCE_EXHAUSTED` on free tier | Exceeded 50k reads/day or 20k writes/day (Spark plan) | Upgrade to Blaze plan; optimize query patterns; cache frequently read documents |
| Reads cost more than expected | `get()` on a collection with 10,000 docs counts as 10,000 reads | Always use `.where()` and `.limit()` to narrow results; paginate large reads |
| Deletes cost more than expected | Deleting a document with subcollections does not delete subcollections | Recursively delete subcollections first; use `firebase firestore:delete --recursive` for CLI deletion |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
