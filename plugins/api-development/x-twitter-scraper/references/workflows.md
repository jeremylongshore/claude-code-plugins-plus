# Xquik Workflow Examples

Code examples for common integration patterns.

## Contents

- [Authentication](#authentication)
- [Retry with Exponential Backoff](#retry-with-exponential-backoff)
- [Cursor Pagination](#cursor-pagination)
- [Complete Extraction Workflow](#complete-extraction-workflow)
- [Real-Time Monitoring Setup](#real-time-monitoring-setup)
- [Endpoint Guide](#endpoint-guide)

## Authentication

```javascript
const apiKey = process.env.XQUIK_API_KEY;
if (!apiKey) throw new Error("Set XQUIK_API_KEY first.");

const BASE = "https://xquik.com/api/v1";
const headers = { "x-api-key": apiKey, "Content-Type": "application/json" };
```

## Retry with Exponential Backoff

Retry only `429` and `5xx`. Never retry `4xx` (except 429). Max 3 retries:

```javascript
async function xquikFetch(path, options = {}) {
  const baseDelay = 1000;

  for (let attempt = 0; attempt <= 3; attempt++) {
    const response = await fetch(`${BASE}${path}`, {
      ...options,
      headers: { ...headers, ...options.headers },
    });

    if (response.ok) return response.json();

    const retryable = response.status === 429 || response.status >= 500;
    if (!retryable || attempt === 3) {
      const error = await response.json();
      throw new Error(`Xquik API ${response.status}: ${error.error}`);
    }

    const retryAfter = response.headers.get("Retry-After");
    const delay = retryAfter
      ? parseInt(retryAfter, 10) * 1000
      : baseDelay * Math.pow(2, attempt) + Math.random() * 1000;

    await new Promise((resolve) => setTimeout(resolve, delay));
  }
}
```

## Cursor Pagination

Events, draws, extractions, and extraction results use cursor-based pagination. When more results exist, the response includes `hasMore: true` and a `nextCursor` string. Pass `nextCursor` as the `after` query parameter.

```javascript
async function fetchAllPages(path, dataKey) {
  const results = [];
  let cursor;

  while (true) {
    const params = new URLSearchParams({ limit: "100" });
    if (cursor) params.set("after", cursor);

    const data = await xquikFetch(`${path}?${params}`);
    results.push(...data[dataKey]);

    if (!data.hasMore) break;
    cursor = data.nextCursor;
  }

  return results;
}
```

Cursors are opaque strings. Never decode or construct them manually.

## Complete Extraction Workflow

```javascript
// Step 1: Estimate usage before running
const estimate = await xquikFetch("/extractions/estimate", {
  method: "POST",
  body: JSON.stringify({
    toolType: "follower_explorer",
    targetUsername: "elonmusk",
    resultsLimit: 1000,
  }),
});

if (!estimate.allowed) {
  console.log(`Estimate requires ${estimate.creditsRequired}; available ${estimate.creditsAvailable}`);
  return;
}

// Step 2: Create extraction job
let job = await xquikFetch("/extractions", {
  method: "POST",
  body: JSON.stringify({
    toolType: "follower_explorer",
    targetUsername: "elonmusk",
    resultsLimit: 1000,
  }),
});

// Step 3: Poll until complete
while (job.status === "pending" || job.status === "running") {
  await new Promise((r) => setTimeout(r, 2000));
  job = await xquikFetch(`/extractions/${job.id}`);
}

// Step 4: Retrieve paginated results (up to 1,000 per page)
let cursor;
const allResults = [];

while (true) {
  const path = `/extractions/${job.id}${cursor ? `?after=${cursor}` : ""}`;
  const page = await xquikFetch(path);
  allResults.push(...page.results);

  if (!page.hasMore) break;
  cursor = page.nextCursor;
}

// Step 5: Export as CSV/JSON/MD/MD-document/PDF/TXT/XLSX (100,000 row limit; PDF 10,000)
const exportUrl = `${BASE}/extractions/${job.id}/export?format=csv`;
const csvResponse = await fetch(exportUrl, { headers });
const csvData = await csvResponse.text();
```

## Real-Time Monitoring Setup

Complete end-to-end: create monitor, register webhook, handle events. Create persistent monitors and webhooks only after explicit user approval of the target, event types, destination URL, and ongoing usage.

```javascript
// 1. Create monitor (persistent resource; active monitors are metered hourly)
const monitor = await xquikFetch("/monitors", {
  method: "POST",
  body: JSON.stringify({
    username: "elonmusk",
    eventTypes: ["tweet.new", "tweet.reply", "tweet.quote", "tweet.retweet"],
  }),
});

// 2. Register webhook (persistent delivery destination)
const webhook = await xquikFetch("/webhooks", {
  method: "POST",
  body: JSON.stringify({
    url: "https://your-server.com/webhook",
    eventTypes: ["tweet.new", "tweet.reply"],
  }),
});
// IMPORTANT: Save webhook.secret. It is shown only once!

// 3. Poll events (alternative to webhooks)
const events = await xquikFetch("/events?monitorId=7&limit=50");
```

Event types: `tweet.new`, `tweet.quote`, `tweet.reply`, `tweet.retweet`, `webhook.test`.

## Endpoint Guide

| Goal | Endpoint | Usage |
|------|----------|------|
| **Get a single tweet** by ID/URL | `GET /x/tweets/{id}` | Metered |
| **Get an X Article** by tweet ID | `GET /x/articles/{tweetId}` | Metered |
| **Search tweets** by keyword/hashtag | `GET /x/tweets/search?q=...` | Metered per result |
| **Get a user profile** | `GET /x/users/{id}` | Metered |
| **Get user's recent tweets** | `GET /x/users/{id}/tweets` | Metered per result |
| **Get user's liked tweets** | `GET /x/users/{id}/likes` | Metered per result |
| **Get user's media tweets** | `GET /x/users/{id}/media` | Metered per result |
| **Get tweet favoriters** | `GET /x/tweets/{id}/favoriters` | Metered per result |
| **Get mutual followers** | `GET /x/users/{id}/followers-you-know` | Metered per result |
| **Check follow relationship** | `GET /x/followers/check?source=A&target=B` | Metered |
| **Get trending topics** | `GET /trends?woeid=1` | Metered |
| **Get radar (trending news)** | `GET /radar?source=hacker_news` | Included |
| **Get bookmarks** | `GET /x/bookmarks` | Metered per result |
| **Get bookmark folders** | `GET /x/bookmarks/folders` | Metered |
| **Get notifications** | `GET /x/notifications` | Metered per result |
| **Get home timeline** | `GET /x/timeline` | Metered per result |
| **Get DM history** | `GET /x/dm/{userId}/history` | Metered per result |
| **Monitor an X account** | `POST /monitors` | Active monitors are metered hourly |
| **Poll for events** | `GET /events` | Included |
| **Receive events via webhook** | `POST /webhooks` | Included; confirmation required for destination URL |
| **Run a giveaway draw** | `POST /draws` | Metered per entry |
| **Download tweet media** | `POST /x/media/download` | Metered per item |
| **Extract bulk data** | `POST /extractions` | Metered per result |
| **Check credits** | `GET /credits` | Included |
| **Compose a tweet** | `POST /compose` | Included |
| **Post a tweet** | `POST /x/tweets` | Metered write action |
| **Like / Unlike a tweet** | `POST` or delete request to `/x/tweets/{id}/like` | Metered write action |
| **Retweet** | `POST /x/tweets/{id}/retweet` | Metered write action |
| **Follow / Unfollow** | `POST` or delete request to `/x/users/{id}/follow` | Metered write action |
| **Send a DM** | `POST /x/dm/{userId}` | Metered write action |
| **Update profile** | `PATCH /x/profile` | Metered write action |
| **Upload media** | `POST /x/media` | Metered write action |
| **Community actions** | `POST /x/communities`, join/leave | Metered write action |
| **Support tickets** | `POST /support/tickets` | Included |
