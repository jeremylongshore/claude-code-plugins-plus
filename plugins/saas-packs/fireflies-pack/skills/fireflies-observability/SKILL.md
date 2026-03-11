---
name: fireflies-observability
description: |
  Set up comprehensive observability for Fireflies.ai integrations with metrics, traces, and alerts.
  Use when implementing monitoring for Fireflies.ai operations, setting up dashboards,
  or configuring alerting for Fireflies.ai integration health.
  Trigger with phrases like "fireflies monitoring", "fireflies metrics",
  "fireflies observability", "monitor fireflies", "fireflies alerts", "fireflies tracing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Fireflies Observability

## Overview
Monitor Fireflies.ai meeting transcription quality, bot join reliability, and transcript processing latency.

## Prerequisites
- Fireflies Business or Enterprise plan
- API access via GraphQL endpoint
- Calendar integration (Google Calendar or Outlook) connected

## Instructions

### Step 1: Monitor Bot Join Reliability
```bash
set -euo pipefail
# Query recent meetings and check bot join status
curl -X POST https://api.fireflies.ai/graphql \
  -H "Authorization: Bearer $FIREFLIES_API_KEY" \
  -d '{"query": "{ transcripts(limit: 50) { id title date duration bot_joined processing_status speakers { name } } }"}' | \
  jq '.data.transcripts[] | {title, date, bot_joined, status: .processing_status, speakers: (.speakers | length)}'
```

### Step 2: Track Transcript Processing Latency
```typescript
// fireflies-metrics.ts
async function monitorProcessing() {
  const res = await firefliesGQL(`{ transcripts(limit: 20) { id date duration processing_status processed_at } }`);
  for (const t of res.data.transcripts) {
    if (t.processing_status === 'completed' && t.processed_at) {
      const meetingEnd = new Date(t.date).getTime() + t.duration * 60000;  # 60000: 1 minute in ms
      const processedAt = new Date(t.processed_at).getTime();
      const processingMinutes = (processedAt - meetingEnd) / 60000;  # 1 minute in ms
      emitHistogram('fireflies_processing_time_min', processingMinutes);
    }
    emitCounter('fireflies_transcripts_total', 1, { status: t.processing_status });
  }
}
```

### Step 3: Measure Per-Seat Utilization
```typescript
// Identify seats with low usage to optimize licensing costs
async function seatUtilization() {
  const members = await firefliesGQL(`{ teamMembers { id email transcripts_count last_active } }`);
  for (const m of members.data.teamMembers) {
    emitGauge('fireflies_seat_usage', m.transcripts_count, { user: m.email });
    if (m.transcripts_count < 5 && daysSince(m.last_active) > 30) {
      console.warn(`Low utilization seat: ${m.email} (${m.transcripts_count} transcripts, inactive ${daysSince(m.last_active)}d)`);
    }
  }
}
```

### Step 4: Alert on Issues
```yaml
groups:
  - name: fireflies
    rules:
      - alert: FirefliesBotNotJoining
        expr: rate(fireflies_transcripts_total{status="bot_failed"}[6h]) > 2
        annotations: { summary: "Fireflies bot failed to join 2+ meetings in 6 hours" }
      - alert: FirefliesProcessingSlow
        expr: histogram_quantile(0.95, rate(fireflies_processing_time_min_bucket[6h])) > 30
        annotations: { summary: "Fireflies transcript processing P95 exceeds 30 minutes" }
      - alert: FirefliesLowSeatUtilization
        expr: count(fireflies_seat_usage < 2) > 5
        annotations: { summary: "5+ Fireflies seats with <2 transcripts (review licensing)" }
```

### Step 5: Dashboard Panels
Track: bot join success rate (pie chart), transcript processing latency distribution, meetings recorded per day, per-seat utilization (table), speaker count distribution, and average meeting duration. Use utilization data to right-size your Fireflies seat count.

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Bot not joining | Calendar permission revoked | Re-authorize calendar integration |
| Transcript stuck processing | Audio quality too poor | Check meeting audio source, avoid Bluetooth |
| No speakers detected | Single audio channel | Enable speaker diarization in settings |
| High seat cost per transcript | Too many inactive seats | Remove members with <2 transcripts/month |

## Examples

**Basic usage**: Apply fireflies observability to a standard project setup with default configuration options.

**Advanced scenario**: Customize fireflies observability for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official monitoring documentation
- Community best practices and patterns
- Related skills in this plugin pack