---
name: juicebox-migration-deep-dive
description: |
  Advanced Juicebox data migration strategies.
  Use when migrating from other recruiting platforms, performing bulk data imports,
  or implementing complex data transformation pipelines.
  Trigger with phrases like "juicebox data migration", "migrate to juicebox",
  "juicebox import", "juicebox bulk migration".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Migration Deep Dive

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview

Migrate candidate data from legacy CRM/ATS systems into Juicebox. Covers data assessment, schema mapping, transformation pipelines, bulk import with rate limiting, validation, and rollback. Check Merge API support first -- Juicebox connects to 50+ ATS/CRM systems directly.

## Prerequisites

- Source system data export capability (CSV, API, or database access)
- Juicebox Enterprise plan (required for bulk import API access)
- `JUICEBOX_USERNAME` and `JUICEBOX_API_TOKEN` environment variables set
- Node.js 18+ (for the transformation pipeline)
- Test Juicebox workspace for dry-run validation

## Migration Sources

| Source | Complexity | Merge API? | Notes |
|--------|------------|------------|-------|
| Greenhouse | Low | Yes | Direct connector via Merge |
| Lever | Low | Yes | Direct connector via Merge |
| LinkedIn Recruiter | Medium | No | Export CSV, map custom fields |
| Bullhorn | Medium | Yes | Large datasets, paginated export |
| Custom ATS | High | No | Custom transformation required |
| CSV/Excel | Low | No | Data quality varies widely |

Check Merge API support first -- if your source ATS is supported, use `juicebox-deploy-integration` instead of manual migration.

## Instructions

### Step 1: Data Assessment

Inventory existing candidate data and score its quality before mapping:

```typescript
// scripts/assess-source-data.ts
import * as fs from "fs";
import { parse } from "csv-parse/sync";

interface DataAssessment {
  totalRecords: number;
  uniqueByEmail: number;
  duplicates: number;
  fieldCoverage: Record<string, { count: number; percent: string }>;
  qualityScore: number;
  estimatedImportTime: string;
}

export function assessSourceData(csvPath: string): DataAssessment {
  const raw = fs.readFileSync(csvPath, "utf-8");
  const records = parse(raw, { columns: true, skip_empty_lines: true });

  const emails = records.map((r: any) => r.email?.toLowerCase().trim()).filter(Boolean);
  const uniqueEmails = new Set(emails);

  const requiredFields = ["name", "email", "title", "company", "location"];
  const fieldCoverage: Record<string, { count: number; percent: string }> = {};

  for (const field of requiredFields) {
    const filled = records.filter(
      (r: any) => r[field] && r[field].trim().length > 0
    ).length;
    fieldCoverage[field] = {
      count: filled,
      percent: ((filled / records.length) * 100).toFixed(1) + "%",
    };
  }

  const weights: Record<string, number> = { name: 0.3, email: 0.3, title: 0.15, company: 0.15, location: 0.1 };
  const qualityScore = Math.round(requiredFields.reduce((s, f) =>
    s + (parseInt(fieldCoverage[f].percent) / 100) * (weights[f] || 0.1), 0) * 100);

  const est = Math.ceil(records.length / 100);
  const assessment: DataAssessment = {
    totalRecords: records.length, uniqueByEmail: uniqueEmails.size,
    duplicates: emails.length - uniqueEmails.size, fieldCoverage,
    qualityScore, estimatedImportTime: est < 60 ? `${est}s` : `${Math.ceil(est / 60)} min`,
  };

  console.table(fieldCoverage);
  console.log(`Quality: ${qualityScore}/100 | Dupes: ${assessment.duplicates} | ETA: ${assessment.estimatedImportTime}`);
  return assessment;
}

// Run: npx tsx scripts/assess-source-data.ts candidates.csv
const csvPath = process.argv[2];
if (csvPath) assessSourceData(csvPath);
```

### Step 2: Schema Mapping

Map legacy CRM fields to Juicebox's profile structure:

```typescript
// lib/migration/schema-mapper.ts
export interface FieldMapping {
  source: string;
  target: string;
  transform?: (value: string) => string;
  required: boolean;
}

// LinkedIn Recruiter CSV -> Juicebox
export const linkedInMapping: FieldMapping[] = [
  { source: "First Name",    target: "first_name",  required: true },
  { source: "Last Name",     target: "last_name",   required: true },
  { source: "Email Address", target: "email",        required: false },
  { source: "Company",       target: "company",      required: false },
  { source: "Title",         target: "title",        required: false },
  { source: "Location",      target: "location",     transform: normalizeLocation, required: false },
  { source: "Profile URL",   target: "linkedin_url", transform: normalizeLinkedInUrl, required: false },
];

// Greenhouse API -> Juicebox
export const greenhouseMapping: FieldMapping[] = [
  { source: "first_name",     target: "first_name",  required: true },
  { source: "last_name",      target: "last_name",   required: true },
  { source: "email_addresses[0].value", target: "email", required: false },
  { source: "company",        target: "company",      required: false },
  { source: "title",          target: "title",        required: false },
];

function normalizeLocation(loc: string): string {
  return loc.replace(/\s+/g, " ").trim().replace(/,\s*USA?$/i, ", United States");
}

function normalizeLinkedInUrl(url: string): string {
  const match = url.match(/linkedin\.com\/in\/([^/?]+)/);
  return match ? `https://www.linkedin.com/in/${match[1]}` : url;
}

export function mapRecord(
  source: Record<string, any>,
  mappings: FieldMapping[]
): Record<string, any> {
  const target: Record<string, any> = {};
  for (const mapping of mappings) {
    let value = source[mapping.source];
    if (value === undefined || value === null || value === "") {
      if (mapping.required) throw new Error(`Required field missing: ${mapping.source}`);
      continue;
    }
    if (mapping.transform) value = mapping.transform(String(value));
    target[mapping.target] = value;
  }
  return target;
}
```

### Step 3: Data Transformation Pipeline

Stream-process large files without loading everything into memory:

```typescript
// lib/migration/pipeline.ts
import { Transform, Readable, Writable, pipeline } from "stream";
import { promisify } from "util";
import { mapRecord, FieldMapping } from "./schema-mapper";

const pipelineAsync = promisify(pipeline);

interface PipelineStats {
  processed: number;
  skipped: number;
  errors: Array<{ line: number; error: string }>;
}

export async function runMigrationPipeline(
  source: Readable,
  destination: Writable,
  mappings: FieldMapping[]
): Promise<PipelineStats> {
  const stats: PipelineStats = { processed: 0, skipped: 0, errors: [] };
  let lineNumber = 0;

  const transformer = new Transform({
    objectMode: true,
    transform(record, _encoding, callback) {
      lineNumber++;
      try {
        const mapped = mapRecord(record, mappings);

        // Deduplicate by email within this batch
        if (mapped.email && this._seenEmails?.has(mapped.email)) {
          stats.skipped++;
          return callback();
        }
        (this._seenEmails ??= new Set()).add(mapped.email);

        stats.processed++;
        this.push(mapped);
        callback();
      } catch (err: any) {
        stats.errors.push({ line: lineNumber, error: err.message });
        stats.skipped++;
        callback(); // Skip bad records, don't halt pipeline
      }
    },
  } as any);

  await pipelineAsync(source, transformer, destination);
  return stats;
}
```

### Step 4: Bulk Import with Rate Limiting

Juicebox's bulk import endpoint accepts batches of up to 100 profiles. Rate-limit to stay under account quotas:

```typescript
// lib/migration/bulk-importer.ts
interface ImportResult {
  total: number;
  created: number;
  updated: number;
  failed: number;
  errors: Array<{ index: number; message: string }>;
}

export class BulkImporter {
  private readonly batchSize = 100;
  private readonly delayMs = 1000; // 1 request per second
  private readonly maxRetries = 3;
  private readonly baseUrl = "https://api.juicebox.ai/v1";

  constructor(
    private username: string,
    private apiToken: string
  ) {}

  async importProfiles(profiles: Record<string, any>[]): Promise<ImportResult> {
    const result: ImportResult = { total: profiles.length, created: 0, updated: 0, failed: 0, errors: [] };

    // Split into batches
    const batches: Record<string, any>[][] = [];
    for (let i = 0; i < profiles.length; i += this.batchSize) {
      batches.push(profiles.slice(i, i + this.batchSize));
    }

    console.log(`Importing ${profiles.length} profiles in ${batches.length} batches...`);

    for (let i = 0; i < batches.length; i++) {
      const batch = batches[i];
      let attempts = 0;
      let success = false;

      while (attempts < this.maxRetries && !success) {
        attempts++;
        try {
          const response = await fetch(`${this.baseUrl}/profiles/bulk`, {
            method: "POST",
            headers: {
              "Authorization": `token ${this.username}:${this.apiToken}`,
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ profiles: batch }),
          });

          if (response.status === 429) {
            const retryAfter = parseInt(response.headers.get("retry-after") || "10", 10);
            console.warn(`Rate limited. Waiting ${retryAfter}s before retry...`);
            await this.delay(retryAfter * 1000);
            continue;
          }

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${await response.text()}`);
          }

          const body = await response.json();
          result.created += body.created || 0;
          result.updated += body.updated || 0;
          result.failed += body.failed || 0;
          if (body.errors) result.errors.push(...body.errors);
          success = true;
        } catch (err: any) {
          if (attempts >= this.maxRetries) {
            result.failed += batch.length;
            result.errors.push({ index: i * this.batchSize, message: err.message });
          }
        }
      }

      // Progress logging
      const pct = (((i + 1) / batches.length) * 100).toFixed(1);
      console.log(`Batch ${i + 1}/${batches.length} (${pct}%) — created: ${result.created}, failed: ${result.failed}`);

      // Rate limit delay between batches
      if (i < batches.length - 1) await this.delay(this.delayMs);
    }

    return result;
  }

  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
```

### Step 5: Validation and Reconciliation

Sample-check 100 records after import to verify data integrity:

```typescript
// scripts/validate-migration.ts
export async function reconcile(
  sourceRecords: Record<string, any>[],
  username: string,
  apiToken: string
): Promise<{ matchRate: string; missing: number; mismatches: number }> {
  const sample = sourceRecords.filter((r) => r.email).slice(0, 100);
  let matched = 0;
  let mismatches = 0;
  const missing: string[] = [];

  for (const record of sample) {
    const response = await fetch(
      `https://api.juicebox.ai/v1/profiles/search?email=${encodeURIComponent(record.email)}`,
      { headers: { "Authorization": `token ${username}:${apiToken}` } }
    );
    if (!response.ok) continue;

    const results = await response.json();
    if (!results.profiles?.length) { missing.push(record.email); continue; }

    matched++;
    const dest = results.profiles[0];
    for (const field of ["name", "company", "title"]) {
      if (record[field]?.trim() && dest[field]?.trim() && record[field].trim() !== dest[field].trim()) {
        mismatches++;
      }
    }
    await new Promise((r) => setTimeout(r, 500)); // Rate limit: 2 req/s
  }

  const matchRate = ((matched / sample.length) * 100).toFixed(1) + "%";
  console.log(`Match rate: ${matchRate} | Missing: ${missing.length} | Mismatches: ${mismatches}`);
  return { matchRate, missing: missing.length, mismatches };
}
```

### Step 6: Rollback Strategy

Tag every imported record with a `migrationId`. Save imported profile IDs to a checkpoint file during import so rollback can delete them:

```typescript
// lib/migration/rollback.ts
import * as fs from "fs";

interface Checkpoint { migrationId: string; profileIds: string[] }

export async function saveCheckpoint(id: string, profileIds: string[]): Promise<void> {
  fs.mkdirSync("./checkpoints", { recursive: true });
  fs.writeFileSync(`./checkpoints/${id}.json`, JSON.stringify({ migrationId: id, profileIds }, null, 2));
}

export async function rollback(id: string, username: string, apiToken: string): Promise<number> {
  const raw = fs.readFileSync(`./checkpoints/${id}.json`, "utf-8");
  const checkpoint: Checkpoint = JSON.parse(raw);
  let deleted = 0;

  for (const profileId of checkpoint.profileIds) {
    const res = await fetch(`https://api.juicebox.ai/v1/profiles/${profileId}`, {
      method: "DELETE",
      headers: { "Authorization": `token ${username}:${apiToken}` },
    });
    if (res.ok) deleted++;
    await new Promise((r) => setTimeout(r, 200));
  }

  console.log(`Rolled back ${deleted}/${checkpoint.profileIds.length} profiles`);
  return deleted;
}
```

## Output

- `scripts/assess-source-data.ts` -- data quality assessment with coverage scoring
- `lib/migration/schema-mapper.ts` -- field mappings for LinkedIn, Greenhouse, and custom sources
- `lib/migration/pipeline.ts` -- streaming transformation pipeline with deduplication
- `lib/migration/bulk-importer.ts` -- rate-limited batch importer with retry logic
- `scripts/validate-migration.ts` -- post-import reconciliation and field comparison
- `lib/migration/rollback.ts` -- checkpoint-based rollback with per-profile deletion

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `Required field missing: First Name` | Source CSV has different column headers | Update `FieldMapping.source` to match actual column names |
| `429 Too Many Requests` during bulk import | Exceeded account rate limit | Increase `delayMs` in BulkImporter; contact Juicebox for temporary limit increase |
| Match rate below 80% after import | Email normalization mismatch | Lowercase and trim emails in both source and validation query |
| `profiles/bulk` returns `403 Forbidden` | Account not on Enterprise plan | Upgrade to Enterprise or use single-profile import endpoint |
| Rollback deletes wrong profiles | Checkpoint file corrupted or missing | Always save checkpoints before starting import; verify `migrationId` tag |

## Examples

**Assess a CSV file before importing:**

```bash
npx tsx scripts/assess-source-data.ts ./data/candidates-export.csv
```

**Run a dry-run import (validate without writing):**

```typescript
const importer = new BulkImporter(process.env.JUICEBOX_USERNAME!, process.env.JUICEBOX_API_TOKEN!);
// Add dry-run flag to skip actual API calls
process.env.DRY_RUN = "true";
const result = await importer.importProfiles(transformedProfiles);
console.log(`Would import ${result.total} profiles (${result.created} new)`);
```

**Migrate from Greenhouse with the Merge API connector:**

```bash
# If Greenhouse is already connected via Merge API, skip manual migration
curl -s -H "Authorization: token ${JUICEBOX_USERNAME}:${JUICEBOX_API_TOKEN}" \
  https://api.juicebox.ai/v1/integrations \
  | jq '.integrations[] | select(.provider == "greenhouse")'
```

## Resources

- [Juicebox Bulk Import Guide](https://juicebox.ai/docs/migration)
- [Juicebox Data Format Specifications](https://juicebox.ai/docs/data-formats)
- [Merge API Integration Directory](https://merge.dev/integrations)
- [Juicebox API Documentation](https://juicebox.ai/docs/api)

## Next Steps

After reconciliation passes, clean up checkpoint files and source exports. Run `juicebox-prod-checklist` for production readiness.
