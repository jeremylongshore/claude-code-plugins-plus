---
name: fathom-cost-tuning
description: |
  Optimize Fathom API usage and plan selection.
  Trigger with phrases like "fathom cost", "fathom pricing", "fathom plan".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom Cost Tuning

## Overview

Fathom pricing scales with per-seat licensing for team features, with primary cost drivers being transcript storage volume and recording hours consumed. Every meeting generates a transcript and AI summary that persist in storage. For organizations running dozens of meetings daily, unchecked transcript accumulation and redundant API polling for meeting data create unnecessary spend. Optimizing retrieval patterns and storage lifecycle directly reduces both API costs and plan overhead.

## Cost Breakdown

| Component | Cost Driver | Optimization |
|-----------|------------|--------------|
| Seat licenses | Per-user/month for Team plan | Audit active seats quarterly; remove inactive users |
| Transcript storage | Accumulated meeting transcripts | Archive transcripts older than 90 days to local storage |
| Recording hours | Meeting duration across all users | Disable recording for standup/informal meetings |
| API polling | Repeated list/get calls for meeting data | Use webhooks for push notifications instead of polling |
| CRM sync events | Per-meeting sync to Salesforce/HubSpot | Batch CRM writes; skip internal-only meetings |

## API Call Reduction

```typescript
class FathomTranscriptCache {
  private cache = new Map<string, { transcript: string; summary: string }>();

  async getTranscript(meetingId: string, apiFn: () => Promise<any>): Promise<any> {
    // Transcripts are immutable after generation — cache permanently
    if (this.cache.has(meetingId)) return this.cache.get(meetingId);
    const result = await apiFn();
    this.cache.set(meetingId, result);
    return result;
  }

  async listMeetings(params: { include_summary: boolean }): Promise<any[]> {
    // Always use include_summary=true to avoid N+1 calls
    // Fetches summaries inline with the list response
    const response = await fetch('/api/meetings?include_summary=true');
    return response.json();
  }
}
```

## Usage Monitoring

```typescript
class FathomUsageTracker {
  private apiCalls = 0;
  private readonly rateLimit = 60; // 60 req/min
  private windowStart = Date.now();

  async throttledCall<T>(fn: () => Promise<T>): Promise<T> {
    if (Date.now() - this.windowStart > 60_000) {
      this.apiCalls = 0;
      this.windowStart = Date.now();
    }
    if (this.apiCalls >= this.rateLimit) {
      const waitMs = 60_000 - (Date.now() - this.windowStart);
      await new Promise(r => setTimeout(r, waitMs));
      this.apiCalls = 0;
      this.windowStart = Date.now();
    }
    this.apiCalls++;
    return fn();
  }

  getUsageReport(): { callsThisMinute: number; remainingCapacity: number } {
    return { callsThisMinute: this.apiCalls, remainingCapacity: this.rateLimit - this.apiCalls };
  }
}
```

## Cost Optimization Checklist

- [ ] Use webhooks for meeting completion events instead of polling
- [ ] Always pass `include_summary=true` in list requests to avoid extra calls
- [ ] Cache transcripts permanently — they never change after generation
- [ ] Batch API processing within the 60 req/min rate limit
- [ ] Audit team seats quarterly and remove inactive users
- [ ] Archive transcripts older than 90 days to reduce storage costs
- [ ] Disable auto-recording for informal or standup meetings
- [ ] Skip CRM sync for internal-only meetings

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 429 rate limit hit | Exceeding 60 req/min | Implement throttling with sliding window |
| Duplicate transcript fetches | Multiple services requesting same meeting | Centralize through shared cache |
| Stale meeting list | Polling on long intervals | Switch to webhook-driven updates |
| CRM sync failures | Batch too large or network timeout | Chunk CRM writes into batches of 10 |
| Storage costs climbing | No transcript lifecycle policy | Implement 90-day archive-to-local policy |

## Resources

- [Fathom Pricing](https://fathom.video/pricing)
- [Fathom API Documentation](https://docs.fathom.video)

## Next Steps

See `fathom-performance-tuning`.
