# Firebase Vertex AI: Examples

## Example 1: Gemini-Backed Chat API on Firebase

Cloud Function accepting user messages, calling Gemini, storing conversation history in Firestore.

```typescript
// functions/src/vertex/chat.ts
import { onCall, HttpsError } from "firebase-functions/v2/https";
import { defineSecret } from "firebase-functions/params";
import { VertexAI } from "@google-cloud/vertexai";
import * as admin from "firebase-admin";

const projectId = defineSecret("GCP_PROJECT_ID");
const db = admin.firestore();

export const chat = onCall(
  { secrets: [projectId], memory: "512MiB", timeoutSeconds: 120 },
  async (req) => {
    if (!req.auth) throw new HttpsError("unauthenticated", "Sign in required");
    const { message, conversationId } = req.data;
    if (!message || typeof message !== "string" || message.length > 4000)
      throw new HttpsError("invalid-argument", "Message must be 1-4000 chars");

    const vertex = new VertexAI({ project: projectId.value(), location: "us-central1" });
    const model = vertex.getGenerativeModel({ model: "gemini-2.5-flash" });

    // Load conversation history
    let history: { role: string; parts: { text: string }[] }[] = [];
    if (conversationId) {
      const convDoc = await db.collection("users").doc(req.auth.uid)
        .collection("conversations").doc(conversationId).get();
      if (convDoc.exists) history = convDoc.data()?.messages || [];
    }

    const chatSession = model.startChat({ history });
    const result = await chatSession.sendMessage(message);
    const responseText = result.response.candidates?.[0]?.content?.parts?.[0]?.text || "";

    // Persist conversation
    const convRef = conversationId
      ? db.collection("users").doc(req.auth.uid).collection("conversations").doc(conversationId)
      : db.collection("users").doc(req.auth.uid).collection("conversations").doc();

    await convRef.set({
      messages: [...history,
        { role: "user", parts: [{ text: message }] },
        { role: "model", parts: [{ text: responseText }] }],
      updatedAt: admin.firestore.FieldValue.serverTimestamp(),
    }, { merge: true });

    return { response: responseText, conversationId: convRef.id };
  }
);
```

Security rule: `match /users/{userId}/conversations/{convId} { allow read, write: if request.auth.uid == userId; }`

Test: `firebase emulators:start --only functions,firestore,auth` then `curl -X POST http://localhost:5001/PROJECT/us-central1/chat -H "Content-Type: application/json" -d '{"data":{"message":"Hello"}}'`

---

## Example 2: Firestore-Powered RAG with Citations

Ingest documents as embeddings, answer questions with source attribution.

```typescript
// Ingestion: Firestore onCreate trigger generates embeddings
export const onDocCreate = onDocumentCreated("documents/{docId}", async (event) => {
  const snap = event.data;
  if (!snap) return;
  const { title, content } = snap.data();

  const vertex = new VertexAI({ project: process.env.GCP_PROJECT_ID!, location: "us-central1" });
  const embedModel = vertex.getGenerativeModel({ model: "text-embedding-004" });
  const result = await embedModel.embedContent({
    content: { role: "user", parts: [{ text: `${title}\n\n${content}` }] },
  });

  await db.collection("embeddings").doc(event.params.docId).set({
    docId: event.params.docId, title,
    vector: result.embedding.values,
    createdAt: admin.firestore.FieldValue.serverTimestamp(),
  });
});

// Query: vector search + Gemini answer
export const ragQuery = onCall({ memory: "1GiB", timeoutSeconds: 180 }, async (req) => {
  if (!req.auth) throw new HttpsError("unauthenticated", "Sign in required");
  const vertex = new VertexAI({ project: process.env.GCP_PROJECT_ID!, location: "us-central1" });

  // Generate query embedding
  const embedModel = vertex.getGenerativeModel({ model: "text-embedding-004" });
  const qEmbed = await embedModel.embedContent({
    content: { role: "user", parts: [{ text: req.data.query }] },
  });

  // Vector search
  const results = await db.collection("embeddings")
    .findNearest("vector", qEmbed.embedding.values, { limit: 5, distanceMeasure: "COSINE" })
    .get();

  // Fetch full docs and generate grounded answer
  const sources = await Promise.all(results.docs.map(async (emb) => {
    const doc = await db.collection("documents").doc(emb.data().docId).get();
    return { id: emb.data().docId, title: emb.data().title, content: doc.data()?.content || "" };
  }));

  const genModel = vertex.getGenerativeModel({ model: "gemini-2.5-flash" });
  const context = sources.map((s, i) => `[${i + 1}] ${s.title}: ${s.content}`).join("\n\n");
  const result = await genModel.generateContent(
    `Answer using sources. Cite as [1], [2].\n\nSources:\n${context}\n\nQuestion: ${req.data.query}`
  );

  return {
    answer: result.response.candidates?.[0]?.content?.parts?.[0]?.text || "",
    sources: sources.map((s, i) => ({ citation: i + 1, title: s.title, id: s.id })),
  };
});
```

---

## Example 3: Content Moderation with Gemini in Firestore Trigger

Auto-moderate user-generated content on write, queue unsafe content for human review.

```typescript
export const moderatePost = onDocumentCreated("posts/{postId}", async (event) => {
  const snap = event.data;
  if (!snap) return;
  const { content, authorId } = snap.data();

  const vertex = new VertexAI({ project: process.env.GCP_PROJECT_ID!, location: "us-central1" });
  const model = vertex.getGenerativeModel({ model: "gemini-2.5-flash" });

  const result = await model.generateContent({
    contents: [{ role: "user", parts: [{ text:
      `Evaluate for safety. Return JSON: {"safe": bool, "categories": string[], "confidence": number, "reason": string}\n\nContent: ${content}`
    }] }],
    generationConfig: { responseMimeType: "application/json" },
  });

  const mod = JSON.parse(result.response.candidates?.[0]?.content?.parts?.[0]?.text || "{}");

  await snap.ref.update({
    moderation: { safe: mod.safe ?? false, categories: mod.categories || [], confidence: mod.confidence || 0 },
    visible: mod.safe === true,
  });

  if (!mod.safe) {
    await db.collection("moderation_queue").add({
      postId: event.params.postId, authorId, reason: mod.reason, flaggedAt: new Date().toISOString(),
    });
  }
});
```

---

## Example 4: Full-Stack Deploy with Auth + Functions + Hosting

Deployment script with environment targeting and smoke tests.

```bash
#!/bin/bash
set -euo pipefail
ENV="${1:-dev}"
firebase use "$ENV"

cd functions && npm ci && npm run build && cd ..
npm run build

# Deploy in dependency order
firebase deploy --only firestore:rules,storage:rules
firebase deploy --only firestore:indexes
firebase deploy --only functions
firebase deploy --only hosting

# Smoke test
PROJECT_ID=$(firebase use | grep -oP 'Active Project: \K\S+' || echo "unknown")
BASE_URL="https://${PROJECT_ID}.web.app"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL")
[ "$HTTP_CODE" = "200" ] && echo "PASS: Hosting OK" || { echo "FAIL: $HTTP_CODE"; exit 1; }
echo "Deployed: $BASE_URL"
```

Required `firebase.json`:

```json
{
  "hosting": {
    "public": "dist",
    "rewrites": [
      { "source": "/api/**", "function": "api" },
      { "source": "**", "destination": "/index.html" }
    ]
  },
  "functions": [{ "source": "functions", "codebase": "default", "runtime": "nodejs20" }],
  "firestore": { "rules": "firestore.rules", "indexes": "firestore.indexes.json" },
  "storage": { "rules": "storage.rules" },
  "emulators": {
    "auth": { "port": 9099 }, "functions": { "port": 5001 },
    "firestore": { "port": 8080 }, "hosting": { "port": 5000 },
    "ui": { "enabled": true, "port": 4000 }
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
