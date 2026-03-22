---
name: langfuse-migration-deep-dive
description: |
  Execute complex Langfuse migrations including data migration and platform changes.
  Use when migrating from other observability platforms, moving between Langfuse instances,
  or performing major infrastructure migrations.
  Trigger with phrases like "langfuse migration", "migrate to langfuse",
  "langfuse data migration", "langfuse platform migration", "switch to langfuse".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langfuse, observability, migration]

---
# Langfuse Migration Deep Dive

## Current State
!`npm list langfuse @langfuse/client 2>/dev/null | head -5 || echo 'No langfuse packages'`

## Overview
Comprehensive guide for complex migrations: cloud-to-self-hosted, LangSmith-to-Langfuse, cross-instance data migration, and zero-downtime dual-write patterns.

## Prerequisites
- Understanding of source and target Langfuse instances
- API keys for both source and target
- Git branch for migration work
- Rollback plan documented

## Migration Scenarios

| Scenario | Complexity | Downtime | Data Loss Risk |
|----------|-----------|----------|----------------|
| Cloud to Cloud (different project) | Low | None | None |
| Cloud to Self-hosted | Medium | Minutes | Low |
| Self-hosted to Cloud | Medium | Minutes | Low |
| LangSmith to Langfuse | High | Hours | Medium |
| SDK v3 to v4+ (no data migration) | Low | None | None |

## Instructions

### Step 1: Export Data from Source Instance

```typescript
// scripts/export-langfuse.ts
import { LangfuseClient } from "@langfuse/client";
import { writeFileSync, mkdirSync } from "fs";

const source = new LangfuseClient({
  publicKey: process.env.SOURCE_LANGFUSE_PUBLIC_KEY,
  secretKey: process.env.SOURCE_LANGFUSE_SECRET_KEY,
  baseUrl: process.env.SOURCE_LANGFUSE_BASE_URL,
});

async function exportAll(outputDir: string) {
  mkdirSync(outputDir, { recursive: true });

  // Export traces
  let page = 1;
  let allTraces: any[] = [];
  let hasMore = true;

  console.log("Exporting traces...");
  while (hasMore) {
    const result = await source.api.traces.list({ limit: 100, page });
    allTraces.push(...result.data);
    hasMore = result.data.length === 100;
    page++;
    await new Promise((r) => setTimeout(r, 200)); // Rate limit
  }
  writeFileSync(`${outputDir}/traces.json`, JSON.stringify(allTraces, null, 2));
  console.log(`  Exported ${allTraces.length} traces`);

  // Export scores
  page = 1;
  let allScores: any[] = [];
  hasMore = true;

  console.log("Exporting scores...");
  while (hasMore) {
    const result = await source.api.scores.list({ limit: 100, page });
    allScores.push(...result.data);
    hasMore = result.data.length === 100;
    page++;
    await new Promise((r) => setTimeout(r, 200));
  }
  writeFileSync(`${outputDir}/scores.json`, JSON.stringify(allScores, null, 2));
  console.log(`  Exported ${allScores.length} scores`);

  // Export prompts
  console.log("Exporting prompts...");
  const prompts = await source.api.prompts.list({ limit: 100 });
  writeFileSync(`${outputDir}/prompts.json`, JSON.stringify(prompts.data, null, 2));
  console.log(`  Exported ${prompts.data.length} prompts`);

  // Export datasets
  console.log("Exporting datasets...");
  const datasets = await source.api.datasets.list({ limit: 100 });
  const fullDatasets = [];
  for (const ds of datasets.data) {
    const items = await source.api.datasetItems.list({ datasetName: ds.name, limit: 1000 });
    fullDatasets.push({ ...ds, items: items.data });
    await new Promise((r) => setTimeout(r, 200));
  }
  writeFileSync(`${outputDir}/datasets.json`, JSON.stringify(fullDatasets, null, 2));
  console.log(`  Exported ${fullDatasets.length} datasets`);
}

exportAll("./migration-export");
```

### Step 2: Import Data to Target Instance

```typescript
// scripts/import-langfuse.ts
import { LangfuseClient } from "@langfuse/client";
import { readFileSync } from "fs";

const target = new LangfuseClient({
  publicKey: process.env.TARGET_LANGFUSE_PUBLIC_KEY,
  secretKey: process.env.TARGET_LANGFUSE_SECRET_KEY,
  baseUrl: process.env.TARGET_LANGFUSE_BASE_URL,
});

async function importAll(inputDir: string) {
  // Import prompts first (no dependencies)
  console.log("Importing prompts...");
  const prompts = JSON.parse(readFileSync(`${inputDir}/prompts.json`, "utf-8"));
  for (const prompt of prompts) {
    await target.api.prompts.create({
      name: prompt.name,
      prompt: prompt.prompt,
      type: prompt.type,
      config: prompt.config,
      labels: prompt.labels,
    });
    console.log(`  Imported prompt: ${prompt.name}`);
    await new Promise((r) => setTimeout(r, 100));
  }

  // Import datasets
  console.log("Importing datasets...");
  const datasets = JSON.parse(readFileSync(`${inputDir}/datasets.json`, "utf-8"));
  for (const ds of datasets) {
    await target.api.datasets.create({
      name: ds.name,
      description: ds.description,
      metadata: { ...ds.metadata, migratedFrom: "source-instance" },
    });

    for (const item of ds.items || []) {
      await target.api.datasetItems.create({
        datasetName: ds.name,
        input: item.input,
        expectedOutput: item.expectedOutput,
        metadata: item.metadata,
      });
      await new Promise((r) => setTimeout(r, 50));
    }
    console.log(`  Imported dataset: ${ds.name} (${ds.items?.length || 0} items)`);
  }

  console.log("Import complete.");
  console.log("Note: Traces and scores are historical -- they reference old trace IDs.");
  console.log("New traces will be created by your application pointing to the target.");
}

importAll("./migration-export");
```

### Step 3: Dual-Write for Zero-Downtime Migration

Write traces to both instances during transition:

```typescript
// src/lib/dual-write-langfuse.ts
import { LangfuseSpanProcessor } from "@langfuse/otel";
import { NodeSDK } from "@opentelemetry/sdk-node";

// Create processors for both instances
const sourceProcessor = new LangfuseSpanProcessor({
  publicKey: process.env.SOURCE_LANGFUSE_PUBLIC_KEY,
  secretKey: process.env.SOURCE_LANGFUSE_SECRET_KEY,
  baseUrl: process.env.SOURCE_LANGFUSE_BASE_URL,
});

const targetProcessor = new LangfuseSpanProcessor({
  publicKey: process.env.TARGET_LANGFUSE_PUBLIC_KEY,
  secretKey: process.env.TARGET_LANGFUSE_SECRET_KEY,
  baseUrl: process.env.TARGET_LANGFUSE_BASE_URL,
});

// Both processors receive all spans
const sdk = new NodeSDK({
  spanProcessors: [sourceProcessor, targetProcessor],
});
sdk.start();

// Migration timeline:
// Week 1: Dual-write enabled, verify target receives traces
// Week 2: Validate data parity between instances
// Week 3: Switch primary to target, keep source as backup
// Week 4: Remove source processor
```

### Step 4: Validate Migration

```typescript
// scripts/validate-migration.ts
import { LangfuseClient } from "@langfuse/client";

const source = new LangfuseClient({
  publicKey: process.env.SOURCE_LANGFUSE_PUBLIC_KEY,
  secretKey: process.env.SOURCE_LANGFUSE_SECRET_KEY,
  baseUrl: process.env.SOURCE_LANGFUSE_BASE_URL,
});

const target = new LangfuseClient({
  publicKey: process.env.TARGET_LANGFUSE_PUBLIC_KEY,
  secretKey: process.env.TARGET_LANGFUSE_SECRET_KEY,
  baseUrl: process.env.TARGET_LANGFUSE_BASE_URL,
});

async function validate() {
  // Compare prompt counts
  const sourcePrompts = await source.api.prompts.list({ limit: 100 });
  const targetPrompts = await target.api.prompts.list({ limit: 100 });
  console.log(`Prompts: source=${sourcePrompts.data.length}, target=${targetPrompts.data.length}`);

  // Compare dataset counts
  const sourceDatasets = await source.api.datasets.list({ limit: 100 });
  const targetDatasets = await target.api.datasets.list({ limit: 100 });
  console.log(`Datasets: source=${sourceDatasets.data.length}, target=${targetDatasets.data.length}`);

  // Compare recent trace counts (dual-write period)
  const since = new Date(Date.now() - 3600000).toISOString();
  const sourceTraces = await source.api.traces.list({ fromTimestamp: since, limit: 100 });
  const targetTraces = await target.api.traces.list({ fromTimestamp: since, limit: 100 });
  console.log(`Recent traces (1h): source=${sourceTraces.data.length}, target=${targetTraces.data.length}`);

  const variance = Math.abs(sourceTraces.data.length - targetTraces.data.length) / Math.max(sourceTraces.data.length, 1);
  console.log(`Trace variance: ${(variance * 100).toFixed(1)}% (target: <5%)`);
}

validate();
```

### Step 5: Cutover and Cleanup

```typescript
// After validation passes:

// 1. Update environment variables to point to target
// LANGFUSE_PUBLIC_KEY=pk-lf-target-...
// LANGFUSE_SECRET_KEY=sk-lf-target-...
// LANGFUSE_BASE_URL=https://target.langfuse.com

// 2. Remove dual-write (use single processor)
const sdk = new NodeSDK({
  spanProcessors: [targetProcessor], // Only target
});

// 3. Keep source instance running for 30 days (rollback window)
// 4. After 30 days, decommission source
```

## Rollback Plan

```bash
set -euo pipefail
# If migration fails, switch back to source:

# 1. Update environment variables
export LANGFUSE_PUBLIC_KEY="pk-lf-source-..."
export LANGFUSE_SECRET_KEY="sk-lf-source-..."
export LANGFUSE_BASE_URL="https://source.langfuse.com"

# 2. Restart application
# 3. Verify traces flowing to source
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Export timeout | Too much data | Paginate with smaller page sizes |
| Import duplicates | Re-running import | Use idempotent creates with unique names |
| Dual-write divergence | One instance failing | Monitor both, alert on variance > 5% |
| Missing prompts | Not exported | Export prompts before datasets |

## Resources
- [Self-Hosting Guide](https://langfuse.com/self-hosting)
- [Upgrade Guide](https://langfuse.com/self-hosting/upgrade)
- [API Reference](https://api.reference.langfuse.com/)
- [v3 to v4 Migration](https://langfuse.com/docs/observability/sdk/upgrade-path/js-v3-to-v4)
