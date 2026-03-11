---
name: firecrawl-enterprise-rbac
description: |
  Configure FireCrawl enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for FireCrawl.
  Trigger with phrases like "firecrawl SSO", "firecrawl RBAC",
  "firecrawl enterprise", "firecrawl roles", "firecrawl permissions", "firecrawl SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# FireCrawl Enterprise RBAC

## Overview
Control access to Firecrawl web scraping and crawling resources through API key management and team credit allocation. Firecrawl uses credit-based pricing where each page scraped costs credits (1 credit for scrape, 5+ for full crawl).

## Prerequisites
- Firecrawl account with Team or Scale plan
- Dashboard access at firecrawl.dev
- Admin-level API key for key management

## Instructions

### Step 1: Create Separate API Keys per Consumer
```bash
set -euo pipefail
# Key for the content indexing pipeline (high volume, crawl access)
curl -X POST https://api.firecrawl.dev/v1/api-keys \
  -H "Authorization: Bearer $FIRECRAWL_ADMIN_KEY" \
  -d '{
    "name": "content-indexer-prod",
    "allowed_endpoints": ["scrape", "crawl", "map"],
    "monthly_credit_limit": 50000  # 50000ms = 50 seconds
  }'

# Key for the sales team (scrape only, limited)
curl -X POST https://api.firecrawl.dev/v1/api-keys \
  -H "Authorization: Bearer $FIRECRAWL_ADMIN_KEY" \
  -d '{
    "name": "sales-prospect-research",
    "allowed_endpoints": ["scrape"],
    "monthly_credit_limit": 5000  # 5000: 5 seconds in ms
  }'
```

### Step 2: Implement a Proxy with Domain Allowlists
```typescript
// firecrawl-gateway.ts
const ALLOWED_DOMAINS: Record<string, string[]> = {
  'sales-team':   ['linkedin.com', 'crunchbase.com', 'g2.com'],
  'content-team': ['*.docs.*', '*.blog.*', 'medium.com'],
  'engineering':  ['*'],  // unrestricted
};

function isDomainAllowed(team: string, url: string): boolean {
  const domain = new URL(url).hostname;
  const patterns = ALLOWED_DOMAINS[team] || [];
  return patterns.some(p => p === '*' || domain.endsWith(p.replace('*', '')));
}
```

### Step 3: Set Credit Alerts
Configure webhook alerts in the Firecrawl dashboard at 50%, 80%, and 95% of monthly credit allocation. This prevents surprise overages from runaway crawl jobs.

### Step 4: Restrict Crawl Depth per Key
```bash
set -euo pipefail
# For the research team, limit crawl depth to prevent multi-thousand page crawls
curl -X POST https://api.firecrawl.dev/v1/crawl \
  -H "Authorization: Bearer $FIRECRAWL_RESEARCH_KEY" \
  -d '{
    "url": "https://docs.example.com",
    "maxDepth": 2,
    "limit": 100,
    "scrapeOptions": {"formats": ["markdown"]}
  }'
```

### Step 5: Audit and Rotate Keys
```bash
set -euo pipefail
# Check credit usage per key
curl https://api.firecrawl.dev/v1/usage \
  -H "Authorization: Bearer $FIRECRAWL_ADMIN_KEY" | \
  jq '.keys[] | {name, credits_used, credits_remaining}'
```
Rotate keys quarterly. Create new key, update consumers, delete old key after 48-hour overlap.

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `402 Payment Required` | Credit limit exhausted | Increase credit limit or wait for cycle reset |
| `403` on `/crawl` endpoint | Key only allows `/scrape` | Create key with crawl permission |
| Crawl job stuck | Target site rate-limiting | Reduce concurrency, add delays |
| Unexpected credit burn | No `limit` set on crawl | Always set `limit` and `maxDepth` |

## Examples

**Basic usage**: Apply firecrawl enterprise rbac to a standard project setup with default configuration options.

**Advanced scenario**: Customize firecrawl enterprise rbac for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official Firecrawl Enterprise Rbac documentation
- Community best practices and patterns
- Related skills in this plugin pack