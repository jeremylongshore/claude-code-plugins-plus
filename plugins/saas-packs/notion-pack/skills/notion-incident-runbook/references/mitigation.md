# Mitigation — Decision Tree and Remediation Code

Step 2 detail: the full classification decision tree, token rotation across secret
managers, the cached fallback pattern for Notion outages, and schema-change detection
for 400 validation errors.

## Decision tree

```
Is status.notion.so showing an incident?
|
+-- YES --> Notion-side outage
|   +-- Enable cached/fallback mode
|   +-- Notify users of degraded service
|   +-- Monitor status page for resolution
|   +-- DO NOT restart or rotate tokens
|
+-- NO --> Our integration issue
    |
    +-- Auth returning 401?
    |   +-- YES --> Token expired or revoked
    |   |   +-- Regenerate at notion.so/my-integrations
    |   |   +-- Update secret manager (see below)
    |   |   +-- Restart application
    |   +-- NO --> Continue
    |
    +-- Getting 429 rate limits?
    |   +-- YES --> Exceeding 3 req/s average
    |   |   +-- Check for runaway loops or webhook storms
    |   |   +-- Reduce concurrency to 1
    |   |   +-- Add exponential backoff
    |   +-- NO --> Continue
    |
    +-- Getting 404 on specific resources?
    |   +-- YES --> Pages unshared or deleted
    |   |   +-- Re-share pages with integration via Connections menu
    |   |   +-- Check if pages were moved to trash
    |   +-- NO --> Continue
    |
    +-- Getting 400 validation errors?
    |   +-- YES --> Database schema changed in Notion UI
    |   |   +-- Re-fetch schema (databases.retrieve)
    |   |   +-- Compare with expected properties
    |   |   +-- Update property mappings in code
    |   +-- NO --> Investigate application logs
```

## Token rotation

```bash
# AWS Secrets Manager
aws secretsmanager update-secret \
  --secret-id notion/production \
  --secret-string '{"token":"ntn_NEW_TOKEN_HERE"}'

# GCP Secret Manager
echo -n "ntn_NEW_TOKEN_HERE" | \
  gcloud secrets versions add notion-token-prod --data-file=-

# Restart to pick up new token
kubectl rollout restart deployment/my-app  # Kubernetes
# or: gcloud run services update my-service --no-traffic  # Cloud Run
```

## Cached fallback for Notion outages

```typescript
import { Client, isNotionClientError } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN! });
const cache = new Map<string, { data: any; timestamp: number }>();
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

async function queryWithFallback(dbId: string, filter?: any) {
  const cacheKey = `query:${dbId}:${JSON.stringify(filter)}`;

  try {
    const result = await notion.databases.query({
      database_id: dbId,
      filter,
      page_size: 100,
    });

    // Update cache on success
    cache.set(cacheKey, { data: result, timestamp: Date.now() });
    return { data: result, source: 'live' as const };
  } catch (error) {
    // Fall back to cache on any API error
    const cached = cache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < CACHE_TTL_MS) {
      console.warn(`Notion unavailable, serving cached data (age: ${
        Math.round((Date.now() - cached.timestamp) / 1000)
      }s)`);
      return { data: cached.data, source: 'cache' as const };
    }

    // No cache available — re-throw
    throw error;
  }
}

// Schema change detection
async function detectSchemaChanges(dbId: string, expectedProps: string[]) {
  const db = await notion.databases.retrieve({ database_id: dbId });
  const actualProps = Object.keys(db.properties);

  const missing = expectedProps.filter(p => !actualProps.includes(p));
  const unexpected = actualProps.filter(p => !expectedProps.includes(p));

  if (missing.length > 0 || unexpected.length > 0) {
    console.error(JSON.stringify({
      event: 'schema_change_detected',
      database_id: dbId,
      missing_properties: missing,
      new_properties: unexpected,
    }));
  }

  return { missing, unexpected, current: actualProps };
}
```
