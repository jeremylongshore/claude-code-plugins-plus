# Firestore Operations Manager: Examples

## Example 1: Fix a Missing Composite Index

Query fails with `FAILED_PRECONDITION: The query requires an index`.

```typescript
// This query needs a composite index on (status ASC, createdAt DESC)
const snapshot = await db.collection("orders")
  .where("status", "==", "pending")
  .orderBy("createdAt", "desc")
  .limit(50).get();
```

The error message includes a Firebase Console URL to auto-create the index. Or add manually to `firestore.indexes.json`:

```json
{
  "indexes": [{
    "collectionGroup": "orders", "queryScope": "COLLECTION",
    "fields": [
      { "fieldPath": "status", "order": "ASCENDING" },
      { "fieldPath": "createdAt", "order": "DESCENDING" }
    ]
  }],
  "fieldOverrides": []
}
```

Deploy: `firebase deploy --only firestore:indexes` then check status with `firebase firestore:indexes` (wait for READY).

**Prevention**: Any `where()` + `orderBy()` on different fields requires a composite index. Single-field queries do not.

---

## Example 2: Batch Migrate 100k Documents with Checkpoints

Add a `status` field (default: `"active"`) to all documents in the `users` collection.

```typescript
import * as admin from "firebase-admin";
admin.initializeApp();
const db = admin.firestore();

const MIGRATION_ID = "add-status-field-2026-03";
const BATCH_SIZE = 500;

interface Checkpoint { lastDocId: string; processed: number; skipped: number; status: string; }

async function getCheckpoint(): Promise<Checkpoint | null> {
  const doc = await db.collection("_migrations").doc(MIGRATION_ID).get();
  return doc.exists ? (doc.data() as Checkpoint) : null;
}

async function saveCheckpoint(cp: Checkpoint): Promise<void> {
  await db.collection("_migrations").doc(MIGRATION_ID).set({
    ...cp, updatedAt: admin.firestore.FieldValue.serverTimestamp(),
  });
}

async function migrate() {
  let checkpoint = await getCheckpoint();
  let processed = checkpoint?.processed || 0;
  let skipped = checkpoint?.skipped || 0;

  while (true) {
    let query = db.collection("users").orderBy("__name__").limit(BATCH_SIZE);
    if (checkpoint?.lastDocId) {
      const lastDoc = await db.collection("users").doc(checkpoint.lastDocId).get();
      if (lastDoc.exists) query = query.startAfter(lastDoc);
    }

    const snapshot = await query.get();
    if (snapshot.empty) break;

    const batch = db.batch();
    let batchCount = 0;
    for (const doc of snapshot.docs) {
      if (doc.data().status !== undefined) { skipped++; continue; } // Idempotent
      batch.update(doc.ref, { status: "active" });
      batchCount++;
    }
    if (batchCount > 0) await batch.commit();
    processed += batchCount;

    const lastDoc = snapshot.docs[snapshot.docs.length - 1];
    checkpoint = { lastDocId: lastDoc.id, processed, skipped, status: "in_progress" };
    await saveCheckpoint(checkpoint);
    console.log(`Processed: ${processed}, Skipped: ${skipped}`);
  }

  await saveCheckpoint({ lastDocId: checkpoint?.lastDocId || "", processed, skipped, status: "completed" });
  console.log(`Done. Processed: ${processed}, Skipped: ${skipped}`);
}
migrate().catch(console.error);
```

Run against emulator first: `FIRESTORE_EMULATOR_HOST=localhost:8080 npx ts-node migrate.ts`

Cost estimate: 100k reads ($0.06) + 100k writes ($0.18) = ~$0.24.

---

## Example 3: Security Rules for Multi-Tenant App

Data model: `tenants/{tenantId}`, `tenants/{tenantId}/members/{userId}`, `tenants/{tenantId}/projects/{projId}`.

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    function isAuth() { return request.auth != null; }
    function isMember(tenantId) {
      return isAuth() && exists(/databases/$(database)/documents/tenants/$(tenantId)/members/$(request.auth.uid));
    }
    function isTenantAdmin(tenantId) {
      return isMember(tenantId) &&
        get(/databases/$(database)/documents/tenants/$(tenantId)/members/$(request.auth.uid)).data.role == 'admin';
    }

    match /tenants/{tenantId} {
      allow read: if isMember(tenantId);
      allow update: if isTenantAdmin(tenantId);
      allow create, delete: if false; // Admin SDK only
    }
    match /tenants/{tenantId}/members/{userId} {
      allow read: if isMember(tenantId);
      allow write: if isTenantAdmin(tenantId);
    }
    match /tenants/{tenantId}/projects/{projId} {
      allow read: if isMember(tenantId);
      allow create: if isMember(tenantId) && request.resource.data.createdBy == request.auth.uid;
      allow update: if isMember(tenantId) && resource.data.createdBy == request.auth.uid;
      allow delete: if isTenantAdmin(tenantId);
    }
  }
}
```

Emulator test:

```typescript
const testEnv = await initializeTestEnvironment({
  projectId: "demo-test", firestore: { rules: readFileSync("firestore.rules", "utf8") },
});
await testEnv.withSecurityRulesDisabled(async (ctx) => {
  await ctx.firestore().doc("tenants/acme").set({ name: "Acme" });
  await ctx.firestore().doc("tenants/acme/members/alice").set({ role: "admin" });
  await ctx.firestore().doc("tenants/acme/members/bob").set({ role: "member" });
});

const alice = testEnv.authenticatedContext("alice");
await assertSucceeds(alice.firestore().doc("tenants/acme").update({ name: "Acme Inc" }));
const bob = testEnv.authenticatedContext("bob");
await assertFails(bob.firestore().doc("tenants/acme").update({ name: "Bob Corp" }));
const eve = testEnv.authenticatedContext("eve");
await assertFails(eve.firestore().doc("tenants/acme").get()); // Not a member
```

---

## Example 4: Cursor-Based Pagination

Fetch products by category, 20 per page, with stable ordering.

```typescript
interface PaginationCursor { lastPrice: number; lastDocId: string; }

async function getProductPage(category: string, pageSize = 20, cursor?: PaginationCursor) {
  let query = db.collection("products")
    .where("category", "==", category)
    .orderBy("price", "asc")
    .orderBy("__name__", "asc")  // Tiebreaker for stable pagination
    .limit(pageSize + 1);        // One extra to detect next page

  if (cursor) query = query.startAfter(cursor.lastPrice, cursor.lastDocId);

  const snapshot = await query.get();
  const hasNextPage = snapshot.docs.length > pageSize;
  const docs = snapshot.docs.slice(0, pageSize);

  return {
    items: docs.map((doc) => ({ id: doc.id, ...doc.data() })),
    nextCursor: hasNextPage
      ? { lastPrice: docs[docs.length - 1].data().price, lastDocId: docs[docs.length - 1].id }
      : null,
    hasNextPage,
  };
}

// Usage
const page1 = await getProductPage("electronics");
if (page1.nextCursor) {
  const page2 = await getProductPage("electronics", 20, page1.nextCursor);
}
```

Required composite index in `firestore.indexes.json`:

```json
{ "collectionGroup": "products", "queryScope": "COLLECTION",
  "fields": [
    { "fieldPath": "category", "order": "ASCENDING" },
    { "fieldPath": "price", "order": "ASCENDING" }
  ]}
```

`__name__` is automatically included as a tiebreaker -- no explicit index entry needed.

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
