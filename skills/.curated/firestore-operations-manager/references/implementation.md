# Firestore Operations Manager: Implementation Guide

## Firestore Data Model Patterns

### Subcollections vs Root Collections

| Pattern | When to Use | Trade-off |
|---------|-------------|-----------|
| Root collection (`/orders`) | Query across all documents regardless of parent | Must store parent IDs as fields; no automatic scoping |
| Subcollection (`/users/{uid}/orders`) | Data naturally owned by a parent; security rules scope by parent | Cannot query across all users' orders without collection group query |
| Collection group query | Cross-parent queries on subcollections | Must create collection group index; same rules apply to all subcollections with that name |

### Denormalization

Firestore has no joins. Duplicate data where read patterns require it:

```typescript
// Store user name directly on order (avoids extra read)
await db.collection("orders").add({
  userId: "alice123", userName: "Alice Smith",
  items: [...], total: 49.99,
  createdAt: admin.firestore.FieldValue.serverTimestamp(),
});

// When name changes, batch-update all denormalized copies
async function updateUserName(userId: string, newName: string) {
  const orders = await db.collection("orders").where("userId", "==", userId).get();
  const BATCH_SIZE = 500;
  for (let i = 0; i < orders.docs.length; i += BATCH_SIZE) {
    const batch = db.batch();
    orders.docs.slice(i, i + BATCH_SIZE).forEach((doc) => batch.update(doc.ref, { userName: newName }));
    await batch.commit();
  }
}
```

## Batch Write Mechanics

### The 500-Operation Limit

Each `WriteBatch.commit()` accepts max 500 operations (`set`, `update`, `delete`). Exceeding throws `INVALID_ARGUMENT`.

### Reusable Chunked Batch Writer

```typescript
async function batchWrite<T>(
  items: T[],
  writeFn: (batch: admin.firestore.WriteBatch, item: T) => void,
  options: { batchSize?: number; onProgress?: (done: number, total: number) => void } = {}
) {
  const { batchSize = 500, onProgress } = options;
  let processed = 0;
  for (let i = 0; i < items.length; i += batchSize) {
    const batch = db.batch();
    items.slice(i, i + batchSize).forEach((item) => writeFn(batch, item));
    await batch.commit();
    processed += Math.min(batchSize, items.length - i);
    onProgress?.(processed, items.length);
  }
  return { processed };
}
```

### Retry Logic

```typescript
async function commitWithRetry(batch: admin.firestore.WriteBatch, maxRetries = 3): Promise<void> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try { await batch.commit(); return; }
    catch (err: any) {
      if (attempt === maxRetries) throw err;
      if (err.code === 10 /* ABORTED */ || err.code === 14 /* UNAVAILABLE */) {
        await new Promise((r) => setTimeout(r, Math.pow(2, attempt) * 1000 + Math.random() * 500));
        continue;
      }
      throw err;
    }
  }
}
```

## Composite Index Design

### When Indexes Are Required

| Query Pattern | Index Needed? |
|---------------|---------------|
| Single `where('field', '==', value)` | No (auto-indexed) |
| Single `where('field', '>', value)` | No (auto-indexed) |
| `where('a', '==', v1).where('b', '==', v2)` | Yes (composite) |
| `where('a', '==', v).orderBy('b')` | Yes (unless a == b) |
| `where('a', '>', v).orderBy('a')` | No (same field) |
| `where('a', '>', v).orderBy('b')` | Yes (a must be first orderBy) |
| `where('a', 'array-contains', v).orderBy('b')` | Yes (composite) |

### Index File Format

```json
{ "indexes": [
  { "collectionGroup": "products", "queryScope": "COLLECTION",
    "fields": [{ "fieldPath": "category", "order": "ASCENDING" }, { "fieldPath": "price", "order": "ASCENDING" }] },
  { "collectionGroup": "orders", "queryScope": "COLLECTION",
    "fields": [{ "fieldPath": "userId", "order": "ASCENDING" }, { "fieldPath": "createdAt", "order": "DESCENDING" }] }
], "fieldOverrides": [] }
```

Deploy: `firebase deploy --only firestore:indexes`. Large collections (>1M docs) can take hours. Deploy indexes before query code.

## Security Rules Testing Workflow

```bash
npm install -D @firebase/rules-unit-testing firebase-admin
```

```typescript
import { initializeTestEnvironment, assertSucceeds, assertFails, RulesTestEnvironment } from "@firebase/rules-unit-testing";
import { readFileSync } from "fs";

let testEnv: RulesTestEnvironment;
beforeAll(async () => {
  testEnv = await initializeTestEnvironment({
    projectId: "demo-test", firestore: { rules: readFileSync("firestore.rules", "utf8") },
  });
});
afterAll(() => testEnv.cleanup());
afterEach(() => testEnv.clearFirestore());

test("owner can read own profile", async () => {
  await testEnv.withSecurityRulesDisabled(async (ctx) => {
    await ctx.firestore().doc("users/alice").set({ name: "Alice", role: "user" });
  });
  await assertSucceeds(testEnv.authenticatedContext("alice").firestore().doc("users/alice").get());
});

test("unauthenticated cannot read profiles", async () => {
  await assertFails(testEnv.unauthenticatedContext().firestore().doc("users/alice").get());
});
```

Run: `firebase emulators:exec --only firestore "npx jest tests/firestore.rules.test.ts"`

## Migration Strategies

### Backfill (Add New Field)

Firestore cannot query for missing fields. Query all, skip docs that already have the field:

```typescript
for (const doc of snapshot.docs) {
  if (doc.data().status !== undefined) { skipped++; continue; }
  batch.update(doc.ref, { status: "active" });
}
```

### Transform (Modify Existing Field)

```typescript
const TRANSFORMS: Record<string, string> = {
  "free": "free_tier", "Free": "free_tier", "premium": "premium_tier", "enterprise": "enterprise_tier",
};
for (const doc of snapshot.docs) {
  const newType = TRANSFORMS[doc.data().type];
  if (!newType || doc.data().type === newType) { skipped++; continue; }
  batch.update(doc.ref, { type: newType });
}
```

### Collection Move

```typescript
async function moveCollection(source: string, target: string) {
  let lastDoc: admin.firestore.DocumentSnapshot | null = null;
  while (true) {
    let query = db.collection(source).orderBy("__name__").limit(500);
    if (lastDoc) query = query.startAfter(lastDoc);
    const snapshot = await query.get();
    if (snapshot.empty) break;
    const batch = db.batch();
    for (const doc of snapshot.docs) {
      batch.set(db.collection(target).doc(doc.id), doc.data());
      batch.delete(doc.ref);
    }
    await batch.commit();
    lastDoc = snapshot.docs[snapshot.docs.length - 1];
  }
}
```

**Warning**: Not atomic across batches. Run reconciliation after failures.

## Emulator Setup

```json
{ "emulators": { "firestore": { "port": 8080 }, "auth": { "port": 9099 }, "ui": { "enabled": true, "port": 4000 } } }
```

Connect Admin SDK:

```typescript
process.env.FIRESTORE_EMULATOR_HOST = "localhost:8080";
process.env.FIREBASE_AUTH_EMULATOR_HOST = "localhost:9099";
admin.initializeApp({ projectId: "demo-test" });
```

Persist data between restarts:

```bash
firebase emulators:start --export-on-exit=./emulator-data --import=./emulator-data
```

Add `emulator-data/` to `.gitignore`.

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
