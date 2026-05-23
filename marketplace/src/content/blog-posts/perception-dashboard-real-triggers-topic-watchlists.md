---
title: "Perception Dashboard: Wiring Real Triggers, Topic Watchlists, and the BSL-1.1 Decision"
description: "How Perception moved from mock ingestion to real Firestore triggers, got an interactive Topic Watchlist, and why I switched from Apache 2.0 to BSL 1.1."
date: "2026-02-10"
tags: ["firebase", "firestore", "mcp", "dashboard", "licensing", "full-stack"]
featured: false
---
## What Perception Does

Perception is a media intelligence dashboard. It ingests articles from 128 RSS feeds, scores them by relevance and trending signals, and surfaces the ones that matter through a React dashboard backed by Firestore and a FastAPI MCP service.

The dashboard existed before February. What didn't exist: real data ingestion, interactive topic management, or auto-ingestion on login. The dashboard was running on mock data. This month, the plumbing got real.

## Mock to Real: The store_articles Trigger

The mock `store_articles` function returned fake results. The real implementation uses Firestore batch writes with URL-based deduplication:

```python
# Document ID: art-{sha256(url)[:16]}
doc_id = f"art-{hashlib.sha256(url.encode()).hexdigest()[:16]}"

# Batch writes with merge=True (preserves AI-enriched fields)
batch = db.batch()
for article in articles[:500]:  # Firestore batch limit
    ref = db.collection('articles').document(doc_id)
    batch.set(ref, article_data, merge=True)
batch.commit()
```

The `merge=True` strategy is deliberate. When the ingestion pipeline re-processes an article, it preserves any AI-enriched fields (summaries, tags, relevance scores) that were added after the initial store. New raw data merges in without overwriting analysis results.

The orchestration endpoint (`POST /trigger/ingestion`) loads all 128 RSS sources from a YAML config, fetches feeds with a 10-item semaphore for concurrency control, stores articles in 500-doc batches, and upserts author metadata. It returns 202 immediately and runs the pipeline in a background task, updating a Firestore `ingestion_runs` document with live phase progress.

Idempotency is built in: if a run is already active, the endpoint returns 409. Stale runs (older than 10 minutes) get auto-cleaned. Success evaluation checks that articles were actually stored, fewer than 50% of sources failed, and the run completed within 5 minutes.

## Auto-Ingestion on Login

The login flow now redirects to `/dashboard` instead of the feed page. On mount, a `useAutoIngestion` hook fires once per browser session:

```typescript
const SESSION_KEY = 'perception-auto-ingestion-fired';

useEffect(() => {
  if (sessionStorage.getItem(SESSION_KEY)) return;
  sessionStorage.setItem(SESSION_KEY, '1');

  fetch(`${MCP_URL}/trigger/ingestion`, {
    method: 'POST',
    body: JSON.stringify({ trigger: 'auto', time_window_hours: 24 }),
  });
}, []);
```

Fire-and-forget. The hook dispatches a custom event that the `IngestionButton` component listens for, showing live progress phases: "Loading sources..." → "Fetching feeds..." → "Storing articles..." → "Done." The button polls every 3 seconds and detects stuck runs with a 5-minute timeout.

The user experience: log in, immediately see fresh articles loading in the background. No manual trigger needed.

## Interactive Topic Watchlist

The Topic Watchlist moved from a static display to full CRUD with real-time Firestore sync:

- **Add topics** with keyword input, category dropdown (16 categories), and source search with autocomplete
- **Multi-select source assignment** per topic — pick which of the 128 feeds should match
- **Delete with hover-reveal** button — no accidental deletions
- **Live metadata** showing "N sources available" and "M topics watching"

```typescript
// Firestore write on topic creation
await setDoc(doc(db, 'topics_to_monitor', topicId), {
  keyword: topicKeyword,
  category: selectedCategory,
  sources: selectedSources,
  created_at: new Date(),
  user_id: auth.currentUser.uid,
});
```

The source search filters against the full 128-source catalog with max 10 results, so the dropdown stays usable. Categories include the obvious ones (ai, engineering, infrastructure) plus niche feeds (hn-popular, crypto, automotive).

## Per-Category Trending

The Articles page now shows the top 3 trending articles per category, scored by a simple algorithm:

```
TrendingScore = RelevanceScore + RecencyBoost + HNBoost

RecencyBoost: 5 points at < 1 hour, decaying to 0 over 24 hours
HNBoost: Every 100 Hacker News points = 1 trending point (capped at 5)
```

The HN integration fetches the top 30 stories and matches by URL against the article database. Articles that are both recent and popular on HN bubble to the top. Articles older than 24 hours lose their recency boost entirely, keeping the trending view fresh.

Category filters show per-category article counts. The Articles page became the default home route — the first thing you see after login is what's trending right now across your monitored topics.

## The BSL-1.1 Decision

Perception moved from Apache 2.0 to Business Source License 1.1. The terms:

- **Change Date**: Four years from publication
- **Change License**: Converts to Apache 2.0 automatically
- **Permitted**: Non-production use (testing, development, research, academic)
- **Restricted**: Commercial repackaging as a competing service

This wasn't a philosophical decision. It was practical. Perception has a real competitive advantage in its RSS source curation (128 feeds), its trending algorithm, and its MCP service architecture. Apache 2.0 lets anyone fork and deploy a competing hosted version immediately. BSL-1.1 gives a four-year commercial window while keeping the code source-available for developers who want to learn from it, build on it, or use it in their own non-competing products.

After four years, it converts to Apache 2.0 automatically. No renewal, no decision needed.

## What I Learned

**Mock-to-real is where architecture gets tested.** The mock ingestion worked because it returned the exact shape the dashboard expected. Real Firestore writes, concurrent feed fetching, and batch limits exposed timing issues and data shape mismatches that mocks hide by design.

**Fire-and-forget with visibility.** The auto-ingestion hook doesn't wait for completion. It fires the trigger and the IngestionButton shows progress independently. This pattern works because the user doesn't need to wait — they can browse existing articles while fresh ones load.

**Session guards prevent duplicate work.** Without the `sessionStorage` guard, every React re-render would fire another ingestion trigger. The guard ensures one trigger per browser session, and the server-side idempotency guard (409 Conflict) catches anything the client misses.
