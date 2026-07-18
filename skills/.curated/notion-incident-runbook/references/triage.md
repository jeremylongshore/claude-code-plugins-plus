# Triage — Full Scripts

Complete triage tooling for Step 1. Run the bash script at first alert to classify
Notion-side vs. integration-side failures; use the TypeScript variant for programmatic
health checks inside your application.

## Bash triage script

Run this diagnostic script to determine if the issue is Notion-side or integration-side:

```bash
#!/bin/bash
# notion-triage.sh — run at first alert
set -euo pipefail
echo "=== Notion Incident Triage ==="
echo "Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1. Check Notion's public status page
echo -e "\n--- Notion Platform Status ---"
STATUS=$(curl -sf https://status.notion.so/api/v2/status.json \
  | jq -r '.status.description' 2>/dev/null || echo "UNREACHABLE")
echo "Notion Status: $STATUS"

INCIDENTS=$(curl -sf https://status.notion.so/api/v2/incidents/unresolved.json \
  | jq '.incidents | length' 2>/dev/null || echo "UNKNOWN")
echo "Active Incidents: $INCIDENTS"

if [ "$INCIDENTS" != "0" ] && [ "$INCIDENTS" != "UNKNOWN" ]; then
  echo "INCIDENT DETAILS:"
  curl -sf https://status.notion.so/api/v2/incidents/unresolved.json \
    | jq -r '.incidents[] | "  - \(.name) (\(.status)): \(.incident_updates[0].body)"'
fi

# 2. Test our integration authentication
echo -e "\n--- Integration Auth Check ---"
AUTH_HTTP=$(curl -sf -o /dev/null -w "%{http_code}" \
  https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" 2>/dev/null || echo "000")   # 2022-06-28 = pinned Notion API version
echo "Auth HTTP Status: $AUTH_HTTP"

if [ "$AUTH_HTTP" = "200" ]; then
  BOT_NAME=$(curl -sf https://api.notion.com/v1/users/me \
    -H "Authorization: Bearer ${NOTION_TOKEN}" \
    -H "Notion-Version: 2022-06-28" | jq -r '.name')
  echo "Bot Name: $BOT_NAME"
fi

# 3. Test database query (if test DB configured)
echo -e "\n--- API Responsiveness ---"
if [ -n "${NOTION_TEST_DATABASE_ID:-}" ]; then
  QUERY_RESULT=$(curl -sf -o /dev/null -w "%{http_code} %{time_total}s" \
    -X POST "https://api.notion.com/v1/databases/${NOTION_TEST_DATABASE_ID}/query" \
    -H "Authorization: Bearer ${NOTION_TOKEN}" \
    -H "Notion-Version: 2022-06-28" \
    -H "Content-Type: application/json" \
    -d '{"page_size": 1}' 2>/dev/null || echo "000 0.000s")
  echo "Database Query: $QUERY_RESULT"
else
  echo "NOTION_TEST_DATABASE_ID not set — skipping query test"
fi

# 4. Classification
echo -e "\n--- Triage Result ---"
if [ "$STATUS" != "All Systems Operational" ] && [ "$STATUS" != "UNREACHABLE" ]; then
  echo "CLASSIFICATION: Notion-side issue. Enable fallback mode."
elif [ "$AUTH_HTTP" = "401" ]; then
  echo "CLASSIFICATION: Token expired or revoked. Rotate immediately."
elif [ "$AUTH_HTTP" = "429" ]; then
  echo "CLASSIFICATION: Rate limited. Reduce concurrency."
elif [ "$AUTH_HTTP" = "000" ]; then
  echo "CLASSIFICATION: Network/DNS issue. Check firewall and DNS."
else
  echo "CLASSIFICATION: Integration-side issue. Check application logs."
fi
```

## TypeScript — programmatic triage

```typescript
import { Client, isNotionClientError, APIErrorCode } from '@notionhq/client';

async function triageNotionHealth(token: string): Promise<{
  classification: string;
  notionStatus: string;
  authStatus: string;
  latencyMs: number;
}> {
  // Check Notion status page
  let notionStatus = 'unknown';
  try {
    const res = await fetch('https://status.notion.so/api/v2/status.json');
    const data = await res.json();
    notionStatus = data.status.description;
  } catch { notionStatus = 'unreachable'; }

  // Test our authentication
  const client = new Client({ auth: token, timeoutMs: 10_000 });
  const start = Date.now();
  let authStatus = 'unknown';
  let classification = 'unknown';

  try {
    await client.users.me({});
    authStatus = 'authenticated';
    classification = 'integration-side';
  } catch (error) {
    if (isNotionClientError(error)) {
      authStatus = `${error.code} (HTTP ${error.status})`;
      switch (error.code) {
        case APIErrorCode.Unauthorized:
          classification = 'token-expired';
          break;
        case APIErrorCode.RateLimited:
          classification = 'rate-limited';
          break;
        case APIErrorCode.ServiceUnavailable:
          classification = 'notion-down';
          break;
        default:
          classification = 'api-error';
      }
    } else {
      authStatus = 'network-error';
      classification = 'network-issue';
    }
  }

  if (notionStatus !== 'All Systems Operational') {
    classification = 'notion-side';
  }

  return {
    classification,
    notionStatus,
    authStatus,
    latencyMs: Date.now() - start,
  };
}
```
