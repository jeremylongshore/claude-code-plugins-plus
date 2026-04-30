---
name: onenote-webhooks-events
description: 'Implement change detection for OneNote using polling and delta queries
  (webhooks decommissioned June 2023).

  Use when building real-time sync, change monitoring, or event-driven OneNote integrations.

  Trigger with "onenote changes", "onenote polling", "onenote sync", "onenote delta
  query".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- onenote
- microsoft
compatibility: Designed for Claude Code
---
# OneNote — Change Detection (Polling & Delta Queries)

## Overview

> **OneNote webhooks were decommissioned June 16, 2023.** The Graph subscription API (`POST /subscriptions` with `changeType: "updated"` on OneNote resources) returns `400 Bad Request`. Unlike Outlook mail, calendar, and OneDrive — which still support push notifications — OneNote has no webhook replacement. You must poll.

This skill implements efficient change detection for OneNote using `lastModifiedDateTime` comparisons, delta query patterns, and rate-limit-aware polling intervals. The approach balances freshness (detecting changes within minutes) against the 600 requests/minute per-user rate limit.

Key pain points addressed:
- Subscription API for OneNote resources returns `400` — do not attempt it
- Delta queries (`/me/onenote/pages/delta`) are not officially documented but work on some tenants
- Polling must stay within rate budget (600/min per user, 10,000/10min per tenant)
- Change detection requires comparing timestamps, not content diffs (output HTML is unstable)

## Prerequisites

- Azure app registration with delegated permissions: `Notes.Read` or `Notes.ReadWrite`
- App-only auth deprecated March 31, 2025 — use delegated auth only
- Python: `pip install msgraph-sdk azure-identity`
- Node/TypeScript: `npm install @microsoft/microsoft-graph-client @azure/identity @azure/msal-node`
- A persistent store for tracking last-seen timestamps (Redis, SQLite, file system)

## Instructions

### Step 1 — Understand Why Webhooks Do Not Work

```typescript
// DO NOT DO THIS — it will return 400 Bad Request
// OneNote webhooks decommissioned June 16, 2023
const subscription = await client.api("/subscriptions").post({
  changeType: "updated",
  notificationUrl: "https://yourapp.com/webhooks/onenote",
  resource: "/me/onenote/pages",  // NOT SUPPORTED
  expirationDateTime: new Date(Date.now() + 3600000).toISOString(),
});
// Error: "Subscription validation request failed. Resource not found."
```

For comparison, these Graph resources still support webhooks: Outlook messages, calendar events, OneDrive files, Teams messages, Planner tasks. OneNote is the notable exception.

### Step 2 — Implement Timestamp-Based Polling (TypeScript)

The core pattern: periodically list pages ordered by `lastModifiedDateTime` and compare against your stored watermark.

```typescript
import { Client } from "@microsoft/microsoft-graph-client";

interface ChangeEvent {
  pageId: string;
  title: string;
  sectionId: string;
  modifiedAt: string;
  changeType: "created" | "modified";
}

class OneNotePoller {
  private watermarks: Map<string, string> = new Map(); // sectionId → ISO timestamp
  private intervalMs: number;
  private timer: NodeJS.Timeout | null = null;
  private client: Client;
  private onChanges: (events: ChangeEvent[]) => void;

  constructor(
    client: Client,
    onChanges: (events: ChangeEvent[]) => void,
    intervalSeconds: number = 30  // Poll every 30s — uses ~2 req/min per section
  ) {
    this.client = client;
    this.onChanges = onChanges;
    this.intervalMs = intervalSeconds * 1000;
  }

  async start(sectionIds: string[]): Promise<void> {
    // Initialize watermarks to "now" to avoid processing historical pages
    const now = new Date().toISOString();
    for (const id of sectionIds) {
      this.watermarks.set(id, now);
    }
    this.timer = setInterval(() => this.poll(sectionIds), this.intervalMs);
    console.log(`Polling ${sectionIds.length} sections every ${this.intervalMs / 1000}s`);
  }

  stop(): void {
    if (this.timer) clearInterval(this.timer);
  }

  private async poll(sectionIds: string[]): Promise<void> {
    const allChanges: ChangeEvent[] = [];

    for (const sectionId of sectionIds) {
      try {
        const watermark = this.watermarks.get(sectionId)!;
        const pages = await this.client.api(
          `/me/onenote/sections/${sectionId}/pages`
        )
          .select("id,title,lastModifiedDateTime,createdDateTime")
          .filter(`lastModifiedDateTime ge ${watermark}`)
          .orderby("lastModifiedDateTime desc")
          .top(50)
          .get();

        for (const page of pages.value ?? []) {
          if (!page.title) continue; // Skip deleted pages (null title)
          const isNew = page.createdDateTime === page.lastModifiedDateTime;
          allChanges.push({
            pageId: page.id,
            title: page.title,
            sectionId,
            modifiedAt: page.lastModifiedDateTime,
            changeType: isNew ? "created" : "modified",
          });
        }

        // Advance watermark
        if (pages.value?.length > 0) {
          this.watermarks.set(sectionId, pages.value[0].lastModifiedDateTime);
        }
      } catch (err: any) {
        if (err.statusCode === 429) {
          const retryAfter = parseInt(err.headers?.["retry-after"] ?? "60", 10);
          console.warn(`Rate limited on section ${sectionId}, backing off ${retryAfter}s`);
          await new Promise((r) => setTimeout(r, retryAfter * 1000));
        } else {
          console.error(`Poll error for section ${sectionId}:`, err.message);
        }
      }
    }

    if (allChanges.length > 0) {
      this.onChanges(allChanges);
    }
  }
}
```

### Step 3 — Rate Budget Planning

With a 600 requests/minute per-user limit, plan your polling capacity:

| Sections Monitored | Poll Interval | Requests/Min | Budget Used |
|---|---|---|---|
| 5 | 30s | 10 | 1.7% |
| 20 | 30s | 40 | 6.7% |
| 50 | 60s | 50 | 8.3% |
| 100 | 60s | 100 | 16.7% |
| 200 | 120s | 100 | 16.7% |

Reserve at least 50% of your rate budget for user-initiated operations (CRUD, search). If monitoring 100+ sections, increase the poll interval to 120s or use the tiered approach below.

### Step 4 — Tiered Polling (Prioritize Active Sections)

Not all sections change equally. Poll recently-active sections more frequently:

```typescript
interface TieredSection {
  id: string;
  tier: "hot" | "warm" | "cold";
  lastChange: Date;
}

function assignTier(lastChange: Date): "hot" | "warm" | "cold" {
  const ageMs = Date.now() - lastChange.getTime();
  const oneHour = 3600_000;
  const oneDay = 86400_000;
  if (ageMs < oneHour) return "hot";     // Changed in last hour
  if (ageMs < oneDay) return "warm";     // Changed in last day
  return "cold";                          // Stale
}

const pollIntervals = {
  hot: 15_000,    // 15 seconds
  warm: 120_000,  // 2 minutes
  cold: 600_000,  // 10 minutes
};
// Re-evaluate tiers after each poll cycle
```

### Step 5 — Python Async Polling

```python
import asyncio
from datetime import datetime, timezone
from msgraph import GraphServiceClient

class OneNotePoller:
    def __init__(self, client: GraphServiceClient, interval_seconds: int = 30):
        self.client = client
        self.interval = interval_seconds
        self.watermarks: dict[str, str] = {}
        self._running = False

    async def start(self, section_ids: list[str], callback):
        """Start polling sections for changes."""
        self._running = True
        now = datetime.now(timezone.utc).isoformat()
        for sid in section_ids:
            self.watermarks[sid] = now

        while self._running:
            changes = []
            for sid in section_ids:
                try:
                    pages = await self.client.me.onenote.sections.by_onenote_section_id(
                        sid
                    ).pages.get()

                    for page in (pages.value or []):
                        if not page.title:
                            continue
                        modified = page.last_modified_date_time.isoformat()
                        if modified > self.watermarks[sid]:
                            changes.append({
                                "page_id": page.id,
                                "title": page.title,
                                "section_id": sid,
                                "modified_at": modified,
                            })
                            self.watermarks[sid] = max(self.watermarks[sid], modified)
                except Exception as e:
                    print(f"Poll error for {sid}: {e}")

            if changes:
                await callback(changes)

            await asyncio.sleep(self.interval)

    def stop(self):
        self._running = False
```

### Step 6 — Event Processing Pipeline

Structure your change handler to decouple detection from processing:

```typescript
interface ChangeProcessor {
  type: string;
  match: (event: ChangeEvent) => boolean;
  handle: (event: ChangeEvent, client: Client) => Promise<void>;
}

const processors: ChangeProcessor[] = [
  {
    type: "sync-to-database",
    match: (e) => e.changeType === "modified",
    handle: async (e, client) => {
      const content = await client.api(`/me/onenote/pages/${e.pageId}/content`).get();
      // Parse HTML, extract structured data, upsert to your DB
    },
  },
  {
    type: "notify-team",
    match: (e) => e.changeType === "created",
    handle: async (e) => {
      // Send Slack/Teams notification for new pages
      console.log(`New page: "${e.title}" in section ${e.sectionId}`);
    },
  },
];

// In your poller callback:
async function processChanges(events: ChangeEvent[], client: Client) {
  for (const event of events) {
    for (const proc of processors) {
      if (proc.match(event)) {
        await proc.handle(event, client);
      }
    }
  }
}
```

## Output

The polling service produces change events with:
- `pageId` — Graph resource ID for the changed page
- `title` — Page title (null for deleted pages, which are filtered out)
- `sectionId` — Parent section identifier
- `modifiedAt` — ISO 8601 timestamp of the change
- `changeType` — `"created"` if `createdDateTime === lastModifiedDateTime`, otherwise `"modified"`

## Error Handling

| Status | Cause | Fix |
|--------|-------|-----|
| 400 | Attempted webhook subscription on OneNote resource | Use polling — webhooks decommissioned June 2023 |
| 429 | Polling too aggressively | Read `Retry-After` header; increase poll interval; use tiered polling |
| 404 | Section deleted between polls | Remove section from poll list; log and continue |
| 502 | Token expired mid-poll | Refresh credentials; MSAL handles this automatically with `DeviceCodeCredential` |
| 500 | Graph service error | Retry with exponential backoff; do not count toward change detection |

## Examples

**Quick start — monitor a single section:**
```typescript
const poller = new OneNotePoller(client, (changes) => {
  changes.forEach((c) => console.log(`[${c.changeType}] ${c.title} at ${c.modifiedAt}`));
}, 30);

await poller.start(["section-id-here"]);
// Output: [modified] Sprint Planning at 2026-03-23T15:30:00Z
```

**Production setup — tiered polling with error recovery:**
```typescript
const sections = await client.api("/me/onenote/notebooks/{id}/sections")
  .select("id,displayName,lastModifiedDateTime")
  .get();

const tiered = sections.value.map((s) => ({
  id: s.id,
  tier: assignTier(new Date(s.lastModifiedDateTime)),
  lastChange: new Date(s.lastModifiedDateTime),
}));

// Start separate pollers per tier
const hotSections = tiered.filter((s) => s.tier === "hot").map((s) => s.id);
const warmSections = tiered.filter((s) => s.tier === "warm").map((s) => s.id);
```

## Resources

- [OneNote API Overview](https://learn.microsoft.com/en-us/graph/api/resources/onenote-api-overview)
- [Integration Guide](https://learn.microsoft.com/en-us/graph/integrate-with-onenote)
- [Best Practices](https://learn.microsoft.com/en-us/graph/onenote-best-practices)
- [Known Issues](https://learn.microsoft.com/en-us/graph/known-issues)
- [Error Codes](https://learn.microsoft.com/en-us/graph/onenote-error-codes)
- [Graph API Reference](https://learn.microsoft.com/en-us/graph/api/overview)

## Next Steps

- See `onenote-rate-limits` for rate budget management when polling many sections
- See `onenote-core-workflow-b` for cross-notebook search if polling detects changes you need to query
- See `onenote-performance-tuning` for caching notebook/section structure to reduce poll overhead
