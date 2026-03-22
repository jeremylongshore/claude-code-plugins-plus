---
name: langfuse-data-handling
description: |
  Manage Langfuse data export, retention, and compliance requirements.
  Use when exporting trace data, configuring retention policies,
  or implementing data compliance for LLM observability.
  Trigger with phrases like "langfuse data export", "langfuse retention",
  "langfuse GDPR", "langfuse compliance", "export langfuse traces".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langfuse, observability, llm, compliance]

---
# Langfuse Data Handling

## Overview
Manage the Langfuse data lifecycle: export traces and scores via the API, configure retention policies, handle GDPR data subject requests, anonymize data for analytics, and maintain audit trails.

## Prerequisites
- `@langfuse/client` installed
- Langfuse API keys with appropriate permissions
- Understanding of your compliance requirements (GDPR, SOC2, HIPAA)

## Instructions

### Step 1: Export Trace Data via API

```typescript
import { LangfuseClient } from "@langfuse/client";
import { writeFileSync } from "fs";

const langfuse = new LangfuseClient();

async function exportTraces(options: {
  fromDate: string;
  toDate: string;
  outputFile: string;
  includeObservations?: boolean;
}) {
  const allTraces: any[] = [];
  let page = 1;
  let hasMore = true;

  while (hasMore) {
    const result = await langfuse.api.traces.list({
      fromTimestamp: options.fromDate,
      toTimestamp: options.toDate,
      limit: 100,
      page,
    });

    for (const trace of result.data) {
      const exportItem: any = {
        id: trace.id,
        name: trace.name,
        timestamp: trace.timestamp,
        userId: trace.userId,
        sessionId: trace.sessionId,
        metadata: trace.metadata,
        tags: trace.tags,
      };

      if (options.includeObservations) {
        const observations = await langfuse.api.observations.list({
          traceId: trace.id,
        });
        exportItem.observations = observations.data;
      }

      allTraces.push(exportItem);
    }

    hasMore = result.data.length === 100;
    page++;

    // Rate limit respect
    await new Promise((r) => setTimeout(r, 200));
  }

  writeFileSync(options.outputFile, JSON.stringify(allTraces, null, 2));
  console.log(`Exported ${allTraces.length} traces to ${options.outputFile}`);
}

// Usage
await exportTraces({
  fromDate: "2025-01-01T00:00:00Z",
  toDate: "2025-01-31T23:59:59Z",
  outputFile: "traces-january.json",
  includeObservations: true,
});
```

### Step 2: Export Scores

```typescript
async function exportScores(fromDate: string, outputFile: string) {
  const scores: any[] = [];
  let page = 1;
  let hasMore = true;

  while (hasMore) {
    const result = await langfuse.api.scores.list({
      fromTimestamp: fromDate,
      limit: 100,
      page,
    });

    scores.push(...result.data);
    hasMore = result.data.length === 100;
    page++;
    await new Promise((r) => setTimeout(r, 200));
  }

  writeFileSync(outputFile, JSON.stringify(scores, null, 2));
  console.log(`Exported ${scores.length} scores to ${outputFile}`);
}
```

### Step 3: Data Retention Configuration

**Self-hosted: Set retention via environment variable:**
```yaml
# docker-compose.yml
services:
  langfuse:
    environment:
      - LANGFUSE_RETENTION_DAYS=90
```

**Cloud: Programmatic cleanup of old data:**
```typescript
async function enforceRetention(maxAgeDays: number) {
  const cutoff = new Date(Date.now() - maxAgeDays * 86400000).toISOString();

  const oldTraces = await langfuse.api.traces.list({
    toTimestamp: cutoff,
    limit: 100,
  });

  console.log(`Found ${oldTraces.data.length} traces older than ${maxAgeDays} days`);

  for (const trace of oldTraces.data) {
    await langfuse.api.traces.delete(trace.id);
    await new Promise((r) => setTimeout(r, 100)); // Rate limit
  }
}

// Run as cron job
await enforceRetention(90);
```

### Step 4: GDPR Data Subject Requests

```typescript
// Handle "Right to Access" -- export all data for a user
async function handleAccessRequest(userId: string) {
  const traces = await langfuse.api.traces.list({
    userId,
    limit: 1000,
  });

  const userData = {
    userId,
    exportDate: new Date().toISOString(),
    traceCount: traces.data.length,
    traces: traces.data.map((t) => ({
      id: t.id,
      name: t.name,
      timestamp: t.timestamp,
      input: t.input,
      output: t.output,
      metadata: t.metadata,
    })),
  };

  writeFileSync(`gdpr-export-${userId}.json`, JSON.stringify(userData, null, 2));
  return userData;
}

// Handle "Right to Erasure" -- delete all data for a user
async function handleDeletionRequest(userId: string) {
  const traces = await langfuse.api.traces.list({
    userId,
    limit: 1000,
  });

  let deleted = 0;
  for (const trace of traces.data) {
    await langfuse.api.traces.delete(trace.id);
    deleted++;
    await new Promise((r) => setTimeout(r, 100));
  }

  console.log(`Deleted ${deleted} traces for user ${userId}`);
  return { userId, tracesDeleted: deleted };
}
```

### Step 5: Data Anonymization for Analytics

```typescript
import crypto from "crypto";

function anonymizeTrace(trace: any): any {
  return {
    ...trace,
    userId: trace.userId ? crypto.createHash("sha256").update(trace.userId).digest("hex").slice(0, 16) : null,
    sessionId: trace.sessionId ? crypto.createHash("sha256").update(trace.sessionId).digest("hex").slice(0, 16) : null,
    input: "[REDACTED]",
    output: "[REDACTED]",
    metadata: {
      model: trace.metadata?.model,
      // Keep operational fields, remove PII
    },
  };
}

async function exportAnonymized(fromDate: string, outputFile: string) {
  const traces = await langfuse.api.traces.list({
    fromTimestamp: fromDate,
    limit: 1000,
  });

  const anonymized = traces.data.map(anonymizeTrace);
  writeFileSync(outputFile, JSON.stringify(anonymized, null, 2));
}
```

## Data Categories and Retention

| Category | Contains PII? | Default Retention | Compliance Note |
|----------|--------------|-------------------|-----------------|
| Traces (inputs/outputs) | Likely | 90 days | Scrub PII before tracing |
| Generations (LLM I/O) | Likely | 90 days | May contain user data |
| Scores | Rarely | 1 year | Typically safe to retain |
| Sessions | User ID linked | 90 days | Link to user data requests |
| Prompts | No | Indefinite | Template data only |
| Datasets | Maybe | Per use case | Review test data for PII |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Export timeout | Too many traces | Reduce date range, use pagination |
| Missing user data | Different userId format | Verify exact userId used in traces |
| Deletion not immediate | Async processing | Allow time for propagation |
| Rate limited during export | Too many API calls | Add 200ms delay between pages |

## Resources
- [Langfuse Data Security](https://langfuse.com/docs/data-security-privacy)
- [Public API Reference](https://langfuse.com/docs/api)
- [API Reference (OpenAPI)](https://api.reference.langfuse.com/)
- [Self-Hosting Configuration](https://langfuse.com/self-hosting/configuration)
