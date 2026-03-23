---
name: notion-policy-guardrails
description: |
  Governance for Notion integrations: integration naming standards, page
  sharing policies, property naming conventions, database schema standards,
  and access audit scripts.
  Trigger with phrases like "notion governance", "notion policy",
  "notion naming convention", "notion access audit", "notion schema standard".
allowed-tools: Read, Write, Edit, Bash(npx:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Policy & Guardrails

## Overview

Governance framework for Notion integrations at scale. Covers integration naming standards for consistent bot identification, page sharing policy enforcement to prevent accidental data exposure, property naming conventions for cross-team database consistency, database schema validation standards, and access audit scripts that scan which integrations have access to which pages. Uses `Client` from `@notionhq/client` for programmatic enforcement.

## Prerequisites

- `@notionhq/client` v2.x installed (`npm install @notionhq/client`)
- Python: `notion-client` installed (`pip install notion-client`)
- `NOTION_TOKEN` environment variable set (admin-level integration recommended for audits)
- CI/CD pipeline (GitHub Actions examples provided)

## Instructions

### Step 1: Integration Naming Standards and Token Management

Establish naming conventions for integrations so teams can identify which bot accessed what.

```typescript
import { Client } from '@notionhq/client';

// Naming convention: {team}-{env}-{purpose}
// Examples: eng-prod-sync, marketing-staging-cms, data-prod-etl

interface IntegrationConfig {
  name: string;           // Must match: /^[a-z]+-[a-z]+-[a-z]+$/
  token: string;
  environment: 'dev' | 'staging' | 'prod';
  owner: string;          // Team or individual
  capabilities: string[]; // What it's allowed to do
}

function validateIntegrationName(name: string): string[] {
  const issues: string[] = [];
  const pattern = /^[a-z]+-[a-z]+-[a-z]+$/;

  if (!pattern.test(name)) {
    issues.push(`Name "${name}" must match pattern: {team}-{env}-{purpose} (e.g., eng-prod-sync)`);
  }

  const [team, env] = name.split('-');
  const validEnvs = ['dev', 'staging', 'prod'];
  if (env && !validEnvs.includes(env)) {
    issues.push(`Environment "${env}" must be one of: ${validEnvs.join(', ')}`);
  }

  return issues;
}

// Validate at startup — fail fast if misconfigured
async function validateIntegration(notion: Client, config: IntegrationConfig): Promise<void> {
  const nameIssues = validateIntegrationName(config.name);
  if (nameIssues.length > 0) {
    throw new Error(`Integration naming violation:\n${nameIssues.join('\n')}`);
  }

  // Verify the token works and matches expected bot name
  const me = await notion.users.me({});
  if (me.type !== 'bot') {
    throw new Error('Token is not a bot integration token');
  }

  console.log(`Integration validated: ${config.name} (bot: ${me.name})`);
}

// Token rotation tracking
interface TokenRegistry {
  integrations: Array<{
    name: string;
    tokenPrefix: string;    // First 8 chars for identification
    createdDate: string;
    rotateBy: string;        // Max 90 days
    owner: string;
  }>;
}

function checkTokenExpiry(registry: TokenRegistry): string[] {
  const warnings: string[] = [];
  const now = new Date();

  for (const integration of registry.integrations) {
    const rotateBy = new Date(integration.rotateBy);
    const daysUntilExpiry = Math.ceil((rotateBy.getTime() - now.getTime()) / 86400000);

    if (daysUntilExpiry < 0) {
      warnings.push(`EXPIRED: ${integration.name} — rotate immediately (expired ${-daysUntilExpiry} days ago)`);
    } else if (daysUntilExpiry < 14) {
      warnings.push(`WARNING: ${integration.name} — expires in ${daysUntilExpiry} days`);
    }
  }

  return warnings;
}
```

### Step 2: Page Sharing Policies and Property Naming Conventions

Enforce which pages can be shared with integrations and standardize property names across databases.

```typescript
// Property naming conventions — enforced via database schema validation
const PROPERTY_NAMING_RULES = {
  // Titles always PascalCase
  title: /^[A-Z][a-zA-Z]+(\s[A-Z][a-zA-Z]+)*$/,
  // Status properties use specific names
  allowedStatusNames: ['Status', 'Stage', 'State'],
  // Date properties end with "Date" or "At"
  date: /Date$|At$/,
  // Relation properties end with target
  relation: /^Related\s|^Parent\s/,
  // Multi-select use plural names
  multi_select: /s$/,
  // Banned property names (too generic)
  banned: ['Data', 'Info', 'Stuff', 'Other', 'Misc', 'Notes2'],
};

async function auditDatabaseSchema(
  notion: Client,
  databaseId: string
): Promise<{ violations: string[]; recommendations: string[] }> {
  const db = await notion.databases.retrieve({ database_id: databaseId });
  const violations: string[] = [];
  const recommendations: string[] = [];

  for (const [name, prop] of Object.entries(db.properties)) {
    // Check banned names
    if (PROPERTY_NAMING_RULES.banned.includes(name)) {
      violations.push(`"${name}": banned property name — use a descriptive name`);
    }

    // Check title format
    if (!PROPERTY_NAMING_RULES.title.test(name)) {
      recommendations.push(`"${name}": consider PascalCase (e.g., "${name.replace(/\b\w/g, c => c.toUpperCase())}")`);
    }

    // Check date naming
    if (prop.type === 'date' && !PROPERTY_NAMING_RULES.date.test(name)) {
      recommendations.push(`"${name}": date properties should end with "Date" or "At" (e.g., "${name} Date")`);
    }

    // Check multi-select naming
    if (prop.type === 'multi_select' && !PROPERTY_NAMING_RULES.multi_select.test(name)) {
      recommendations.push(`"${name}": multi-select properties should use plural names (e.g., "${name}s")`);
    }
  }

  // Check for required properties
  const propTypes = Object.entries(db.properties).map(([name, prop]) => ({ name, type: prop.type }));
  const hasTitle = propTypes.some(p => p.type === 'title');
  if (!hasTitle) {
    violations.push('Database must have a title property');
  }

  return { violations, recommendations };
}

// Page sharing policy: audit which pages are accessible
async function auditPageAccess(
  notion: Client,
  databaseId: string
): Promise<void> {
  console.log('=== Page Access Audit ===');

  const response = await notion.databases.query({
    database_id: databaseId,
    page_size: 100,
  });

  for (const page of response.results) {
    if (!('parent' in page)) continue;
    const pageObj = page as any;

    // Check if page has public URL (shared publicly)
    if (pageObj.public_url) {
      console.warn(`PUBLIC PAGE: ${page.id} — ${pageObj.public_url}`);
    }

    // Log page access for audit trail
    console.log(`Page ${page.id}: parent=${pageObj.parent.type}, created=${pageObj.created_time}`);
  }
}
```

```python
from notion_client import Client

notion = Client(auth=os.environ["NOTION_TOKEN"])

def audit_database_schema(database_id: str) -> dict:
    """Validate database schema against naming conventions."""
    db = notion.databases.retrieve(database_id=database_id)
    violations = []
    recommendations = []

    banned_names = {"Data", "Info", "Stuff", "Other", "Misc"}

    for name, prop in db["properties"].items():
        if name in banned_names:
            violations.append(f'"{name}": banned property name')

        if prop["type"] == "date" and not (name.endswith("Date") or name.endswith("At")):
            recommendations.append(f'"{name}": date properties should end with Date/At')

        if prop["type"] == "multi_select" and not name.endswith("s"):
            recommendations.append(f'"{name}": multi-select should use plural name')

    return {"violations": violations, "recommendations": recommendations}
```

### Step 3: Access Audit Scripts and Database Schema Standards

Comprehensive audit of what integrations can access across your workspace, plus CI-enforced schema validation.

```typescript
// Full workspace access audit
async function workspaceAccessAudit(notion: Client): Promise<void> {
  console.log('=== Workspace Access Audit ===');
  console.log(`Timestamp: ${new Date().toISOString()}`);

  // 1. Identify the integration
  const me = await notion.users.me({});
  console.log(`\nIntegration: ${me.name} (${me.id})`);

  // 2. Search all accessible content
  const allContent: Array<{ type: string; id: string; title: string }> = [];
  let cursor: string | undefined;

  do {
    const search = await notion.search({
      page_size: 100,
      start_cursor: cursor,
    });

    for (const result of search.results) {
      const obj = result as any;
      let title = 'Untitled';

      if (obj.object === 'page' && obj.properties) {
        const titleProp = Object.values(obj.properties).find((p: any) => p.type === 'title') as any;
        title = titleProp?.title?.[0]?.plain_text ?? 'Untitled';
      } else if (obj.object === 'database') {
        title = obj.title?.[0]?.plain_text ?? 'Untitled DB';
      }

      allContent.push({ type: obj.object, id: obj.id, title });
    }

    cursor = search.has_more ? (search.next_cursor ?? undefined) : undefined;
    await new Promise(r => setTimeout(r, 350)); // Rate limit
  } while (cursor);

  // 3. Report
  const pages = allContent.filter(c => c.type === 'page');
  const databases = allContent.filter(c => c.type === 'database');

  console.log(`\nAccessible content:`);
  console.log(`  Pages: ${pages.length}`);
  console.log(`  Databases: ${databases.length}`);
  console.log(`  Total: ${allContent.length}`);

  console.log(`\nDatabases accessible:`);
  for (const db of databases) {
    console.log(`  - ${db.title} (${db.id})`);
  }

  // 4. Flag concerns
  if (allContent.length > 1000) {
    console.warn('\nWARNING: Integration has access to >1000 items. Review sharing scope.');
  }
}

// CI check: validate database schema matches expected standard
// Run in CI after any schema changes
async function validateSchemaInCI(
  notion: Client,
  schemas: Record<string, { requiredProperties: Record<string, string>; database_id: string }>
): Promise<{ passed: boolean; issues: string[] }> {
  const issues: string[] = [];

  for (const [schemaName, config] of Object.entries(schemas)) {
    const db = await notion.databases.retrieve({ database_id: config.database_id });

    for (const [propName, expectedType] of Object.entries(config.requiredProperties)) {
      const actual = db.properties[propName];

      if (!actual) {
        issues.push(`${schemaName}: missing required property "${propName}"`);
      } else if (actual.type !== expectedType) {
        issues.push(`${schemaName}: "${propName}" should be ${expectedType}, got ${actual.type}`);
      }
    }

    // Run naming convention audit
    const audit = await auditDatabaseSchema(notion, config.database_id);
    issues.push(...audit.violations.map(v => `${schemaName}: ${v}`));
  }

  return { passed: issues.length === 0, issues };
}

// GitHub Actions workflow for schema validation
// .github/workflows/notion-policy.yml
const workflowYaml = `
name: Notion Policy Check
on:
  schedule:
    - cron: '0 9 * * 1'  # Weekly Monday 9am
  workflow_dispatch:

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - name: Run access audit
        env:
          NOTION_TOKEN: \${{ secrets.NOTION_AUDIT_TOKEN }}
        run: npx ts-node scripts/notion-access-audit.ts

      - name: Scan for leaked tokens
        run: |
          if grep -rE "(ntn_|secret_)[a-zA-Z0-9]{30,}" \\
            --include="*.ts" --include="*.js" --include="*.json" \\
            --exclude-dir=node_modules --exclude-dir=.git .; then
            echo "::error::Notion token found in source code"
            exit 1
          fi
`;
```

```python
def workspace_access_audit():
    """Audit all content accessible to this integration."""
    me = notion.users.me()
    print(f"Integration: {me['name']} ({me['id']})")

    all_content = []
    cursor = None

    while True:
        kwargs = {"page_size": 100}
        if cursor:
            kwargs["start_cursor"] = cursor

        results = notion.search(**kwargs)
        all_content.extend(results["results"])

        if not results.get("has_more"):
            break
        cursor = results.get("next_cursor")

    pages = [c for c in all_content if c["object"] == "page"]
    databases = [c for c in all_content if c["object"] == "database"]

    print(f"\nAccessible: {len(pages)} pages, {len(databases)} databases")

    if len(all_content) > 1000:
        print("WARNING: Integration has broad access. Review sharing scope.")

    return {"pages": len(pages), "databases": len(databases), "total": len(all_content)}
```

## Output

- Integration naming standards validated at startup
- Token rotation tracking with expiry warnings
- Property naming conventions audited against database schemas
- Access audit showing all content visible to the integration
- CI workflow enforcing schema standards and secret scanning
- Violation report with actionable recommendations

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Audit shows too many pages | Integration shared at workspace level | Narrow sharing to specific pages/databases |
| Schema validation fails | Property renamed in Notion UI | Update schema config to match |
| Token scan false positive | Test fixtures contain example tokens | Add `--exclude` for test directories |
| `object_not_found` during audit | Page unshared since last audit | Expected — log and continue |
| Naming convention too strict | Legacy integrations don't match | Add exceptions list with migration deadline |

## Examples

### Quick Compliance Check

```bash
# One-line secret scan for CI
grep -rn "ntn_\|secret_" --include="*.ts" --include="*.js" src/ && echo "FAIL: Token found" || echo "PASS: No tokens"

# Check .env files not committed
git ls-files | grep -E "^\.env" && echo "FAIL: .env committed" || echo "PASS"
```

### Schema Registry

```typescript
// Define expected schemas for CI validation
const SCHEMA_REGISTRY = {
  tasks: {
    database_id: process.env.NOTION_TASKS_DB!,
    requiredProperties: {
      'Name': 'title',
      'Status': 'select',
      'Assignee': 'people',
      'Due Date': 'date',
      'Priority': 'select',
    },
  },
  content: {
    database_id: process.env.NOTION_CONTENT_DB!,
    requiredProperties: {
      'Title': 'title',
      'Status': 'select',
      'Published Date': 'date',
      'Author': 'people',
      'Tags': 'multi_select',
    },
  },
};
```

## Resources

- [Notion Integration Best Practices](https://developers.notion.com/docs/best-practices-for-handling-api-keys)
- [Notion Authorization Guide](https://developers.notion.com/docs/authorization)
- [ESLint Custom Rules](https://eslint.org/docs/latest/extend/plugins)
- [Pre-commit Framework](https://pre-commit.com/)

## Next Steps

For architecture blueprints, see `notion-architecture-variants`.
For common mistakes to avoid, see `notion-known-pitfalls`.
