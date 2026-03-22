---
name: notion-advanced-troubleshooting
description: |
  Apply advanced Notion API debugging techniques for hard-to-diagnose issues.
  Use when standard troubleshooting fails, investigating race conditions,
  or preparing evidence for Notion developer support.
  Trigger with phrases like "notion hard bug", "notion mystery error",
  "notion impossible to debug", "difficult notion issue", "notion deep debug".
allowed-tools: Read, Grep, Bash(curl:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Advanced Troubleshooting

## Overview
Deep debugging techniques for Notion API issues that resist standard troubleshooting: request tracing, response inspection, timing analysis, and evidence collection.

## Prerequisites
- Access to application logs
- `@notionhq/client` with debug logging enabled
- `curl` for raw API testing
- Understanding of HTTP and JSON

## Instructions

### Step 1: Enable SDK Debug Logging
```typescript
import { Client, LogLevel } from '@notionhq/client';

// Enable full request/response logging
const notion = new Client({
  auth: process.env.NOTION_TOKEN,
  logLevel: LogLevel.DEBUG, // Logs every request and response
});
```

### Step 2: Raw API Testing (Bypass SDK)
```bash
# Test the exact endpoint that's failing
# This isolates SDK issues from API issues

# Retrieve a page
curl -v https://api.notion.com/v1/pages/PAGE_ID \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" \
  2>&1 | tee /tmp/notion-debug.log

# Query a database with filter
curl -v -X POST https://api.notion.com/v1/databases/DB_ID/query \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{
    "filter": {
      "property": "Status",
      "select": { "equals": "Done" }
    },
    "page_size": 1
  }' 2>&1 | tee /tmp/notion-query-debug.log

# Create a page (minimal)
curl -v -X POST https://api.notion.com/v1/pages \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": { "database_id": "DB_ID" },
    "properties": {
      "Name": { "title": [{ "text": { "content": "Debug test" } }] }
    }
  }' 2>&1 | tee /tmp/notion-create-debug.log

# Check response headers (rate limit info, request ID)
grep -i "x-request-id\|retry-after\|x-ratelimit" /tmp/notion-debug.log
```

### Step 3: Request ID Tracking
Every Notion API response includes an `x-request-id` header. Capture it for support tickets:

```typescript
import { isNotionClientError } from '@notionhq/client';

async function debugNotionCall<T>(label: string, fn: () => Promise<T>): Promise<T> {
  const start = Date.now();
  try {
    const result = await fn();
    console.log(`[${label}] OK in ${Date.now() - start}ms`);
    return result;
  } catch (error) {
    if (isNotionClientError(error)) {
      console.error(`[${label}] FAILED in ${Date.now() - start}ms`, {
        code: error.code,
        status: error.status,
        message: error.message,
        // The request ID is in error.headers if available
        requestId: error.headers?.['x-request-id'] ?? 'unknown',
        body: error.body,
      });
    }
    throw error;
  }
}

// Usage
const page = await debugNotionCall('retrieve-page', () =>
  notion.pages.retrieve({ page_id: pageId })
);
```

### Step 4: Property Schema Mismatch Detection
The most common validation errors come from property name/type mismatches:

```typescript
async function validatePropertiesAgainstSchema(
  databaseId: string,
  properties: Record<string, any>
) {
  const db = await notion.databases.retrieve({ database_id: databaseId });
  const schema = db.properties;
  const issues: string[] = [];

  for (const [propName, propValue] of Object.entries(properties)) {
    const schemaProp = schema[propName];

    if (!schemaProp) {
      issues.push(`Property "${propName}" does not exist in database. Available: ${Object.keys(schema).join(', ')}`);
      continue;
    }

    // Check type matches
    if (propValue && typeof propValue === 'object') {
      const valueType = Object.keys(propValue).find(k =>
        ['title', 'rich_text', 'number', 'select', 'multi_select', 'date', 'checkbox', 'url', 'email', 'phone_number', 'people', 'relation'].includes(k)
      );
      if (valueType && valueType !== schemaProp.type) {
        issues.push(`Property "${propName}" is type "${schemaProp.type}" but you sent type "${valueType}"`);
      }
    }
  }

  // Check for missing title
  const titleProp = Object.entries(schema).find(([, v]) => v.type === 'title');
  if (titleProp && !properties[titleProp[0]]) {
    issues.push(`Missing required title property "${titleProp[0]}"`);
  }

  if (issues.length > 0) {
    console.error('Property validation issues:');
    issues.forEach(i => console.error(`  - ${i}`));
  }

  return { valid: issues.length === 0, issues };
}
```

### Step 5: Timing Analysis
```typescript
class NotionTimingAnalyzer {
  private timings: Map<string, number[]> = new Map();

  async measure<T>(operation: string, fn: () => Promise<T>): Promise<T> {
    const start = performance.now();
    try {
      return await fn();
    } finally {
      const duration = performance.now() - start;
      const existing = this.timings.get(operation) || [];
      existing.push(duration);
      this.timings.set(operation, existing);
    }
  }

  report() {
    for (const [op, times] of this.timings) {
      const sorted = [...times].sort((a, b) => a - b);
      console.log(`${op}:`, {
        count: times.length,
        min: Math.round(sorted[0]),
        p50: Math.round(sorted[Math.floor(sorted.length * 0.5)]),
        p95: Math.round(sorted[Math.floor(sorted.length * 0.95)]),
        max: Math.round(sorted[sorted.length - 1]),
        avg: Math.round(times.reduce((a, b) => a + b) / times.length),
      });
    }
  }
}

// Usage
const timer = new NotionTimingAnalyzer();
for (let i = 0; i < 10; i++) {
  await timer.measure('databases.query', () =>
    notion.databases.query({ database_id: dbId, page_size: 1 })
  );
}
timer.report();
```

### Step 6: Minimal Reproduction
```typescript
// Strip everything down to the absolute minimum failing case
async function minimalRepro() {
  const notion = new Client({
    auth: process.env.NOTION_TOKEN,
    logLevel: LogLevel.DEBUG,
  });

  // Test 1: Can we authenticate?
  console.log('Test 1: Auth');
  const me = await notion.users.me({});
  console.log('  Bot:', me.name, me.type);

  // Test 2: Can we search?
  console.log('Test 2: Search');
  const search = await notion.search({ page_size: 1 });
  console.log('  Results:', search.results.length);

  // Test 3: Can we query the specific database?
  console.log('Test 3: Database query');
  const query = await notion.databases.query({
    database_id: process.env.NOTION_DB_ID!,
    page_size: 1,
  });
  console.log('  Pages:', query.results.length);

  // Test 4: The specific failing operation
  console.log('Test 4: Failing operation');
  // ... insert the exact failing call here
}

minimalRepro().catch(error => {
  console.error('Repro failed at:', error.message);
  if (isNotionClientError(error)) {
    console.error('  Code:', error.code);
    console.error('  Status:', error.status);
    console.error('  Body:', JSON.stringify(error.body, null, 2));
  }
});
```

## Output
- Debug logging enabled for full request/response visibility
- Raw API testing results (bypassing SDK)
- Request IDs captured for support tickets
- Property schema validation results
- Timing analysis identifying latency bottlenecks
- Minimal reproduction case

## Error Handling
| Issue | Debug Approach |
|-------|---------------|
| Intermittent 400 errors | Property schema validation + timing analysis |
| Slow responses | Timing analysis across operations |
| Works in curl, fails in SDK | Compare headers and payload exactly |
| Works locally, fails in CI | Environment comparison (token, network) |
| Random 404s | Check if pages are being concurrently archived |

## Examples

### Support Escalation Template
```
Subject: [Request ID: xxx] [Error Code] on [Operation]

Environment: Node.js X, @notionhq/client X.Y.Z, API version 2022-06-28
Integration ID: [from notion.so/my-integrations]
Request ID: [from x-request-id header]
Timestamp: [ISO 8601]

Reproduction:
curl -X POST https://api.notion.com/v1/... [exact command]

Expected: [behavior]
Actual: [error code + message]

Frequency: [every time / intermittent / started on date]
```

## Resources
- [Notion Developer Community](https://developers.notion.com)
- [Notion API Introduction](https://developers.notion.com/reference/intro)
- [Notion Status Page](https://status.notion.com)
- [GitHub: notion-sdk-js Issues](https://github.com/makenotion/notion-sdk-js/issues)

## Next Steps
For load testing, see `notion-load-scale`.
