---
name: clay-enterprise-rbac
description: |
  Configure Clay workspace roles, team access control, and credit budget allocation.
  Use when managing team access to Clay tables, setting per-user credit budgets,
  or configuring workspace-level permissions for Clay.
  Trigger with phrases like "clay SSO", "clay RBAC", "clay enterprise",
  "clay roles", "clay permissions", "clay team access", "clay workspace".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, rbac]

---
# Clay Enterprise RBAC

## Overview

Control access to Clay tables, enrichment credits, and integrations at the team level. Clay uses a workspace model where team members are assigned Admin, Member, or Viewer roles. This skill covers role assignment, credit budget allocation, API key isolation, and audit procedures.

## Prerequisites

- Clay Team or Enterprise plan
- Workspace admin privileges
- Understanding of team structure and data access needs

## Instructions

### Step 1: Define Role Matrix

Clay has three built-in roles with fixed permissions:

| Capability | Admin | Member | Viewer |
|------------|-------|--------|--------|
| Manage workspace members | Yes | No | No |
| Manage billing and credits | Yes | No | No |
| Create/delete tables | Yes | Yes | No |
| Run enrichments | Yes | Yes | No |
| Configure integrations | Yes | No | No |
| Export data | Yes | Yes | Yes |
| View all tables | Yes | Yes | Yes |

**Recommended role assignments:**

```yaml
roles:
  admin:
    assign_to:
      - Revenue Operations Lead
      - GTM Engineering Lead
    why: "Controls billing, integrations, and team access"

  member:
    assign_to:
      - SDRs building prospect lists
      - Growth engineers building pipelines
      - Marketing ops running enrichment campaigns
    why: "Can create tables and run enrichments but can't change billing or integrations"

  viewer:
    assign_to:
      - Sales managers reviewing lead quality
      - Executives checking pipeline metrics
      - Finance reviewing credit usage
    why: "Read-only access to enriched data and exports"
```

### Step 2: Invite and Manage Team Members

In Clay UI: **Settings > Members > Invite**

Best practices:
- Use company email addresses (not personal)
- Start new members as Viewers until they complete Clay training
- Audit member list quarterly -- remove departed employees immediately

### Step 3: Isolate API Keys by Integration

Create separate API keys for each downstream system to enable independent revocation:

```yaml
api_keys:
  crm-sync-prod:
    purpose: "HubSpot CRM sync from Clay"
    used_by: "HTTP API column in Outbound Leads table"
    rotation: quarterly

  outbound-instantly:
    purpose: "Push qualified leads to Instantly.ai"
    used_by: "HTTP API column for outreach"
    rotation: quarterly

  internal-dashboard:
    purpose: "Pull enrichment metrics for internal dashboard"
    used_by: "Cron job reading Clay table stats"
    rotation: quarterly

  ci-testing:
    purpose: "Integration tests in CI pipeline"
    used_by: "GitHub Actions workflow"
    rotation: on-demand
```

### Step 4: Set Credit Budget Controls

Since Clay doesn't have per-user credit budgets natively, implement controls at the table level:

```typescript
// src/clay/budget-controls.ts
interface TableBudget {
  tableId: string;
  tableName: string;
  maxRows: number;           // Prevent over-enrichment
  autoEnrich: boolean;       // Control automatic processing
  owner: string;             // Team member responsible
  monthlyCreditsEstimate: number;
}

const TABLE_BUDGETS: TableBudget[] = [
  {
    tableId: 'outbound-leads',
    tableName: 'Outbound Leads',
    maxRows: 5000,
    autoEnrich: true,
    owner: 'sdr-team@company.com',
    monthlyCreditsEstimate: 3000,
  },
  {
    tableId: 'event-attendees',
    tableName: 'Event Attendees',
    maxRows: 1000,
    autoEnrich: false,  // Manual trigger only
    owner: 'marketing@company.com',
    monthlyCreditsEstimate: 600,
  },
  {
    tableId: 'inbound-leads',
    tableName: 'Inbound Leads',
    maxRows: 2000,
    autoEnrich: true,
    owner: 'growth-eng@company.com',
    monthlyCreditsEstimate: 1200,
  },
];

function auditBudgets(budgets: TableBudget[]): void {
  const totalEstimate = budgets.reduce((sum, b) => sum + b.monthlyCreditsEstimate, 0);
  console.log(`=== Clay Credit Budget Audit ===`);
  for (const b of budgets) {
    console.log(`  ${b.tableName}: ${b.maxRows} rows, ~${b.monthlyCreditsEstimate} credits/mo (owner: ${b.owner})`);
  }
  console.log(`  Total monthly estimate: ${totalEstimate} credits`);
}
```

### Step 5: Quarterly Access Audit

```markdown
## Clay Workspace Access Audit Checklist

- [ ] Review all workspace members — remove former employees
- [ ] Verify role assignments match current job functions
- [ ] Check API key usage — revoke unused keys
- [ ] Review table access — archive unused tables
- [ ] Audit credit usage by table — identify waste
- [ ] Verify provider API key connections are current
- [ ] Update API key rotation log
- [ ] Review and update table row limits
- [ ] Check webhook submission counts (approaching 50K?)
- [ ] Document any new tables or integrations added
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `403` on table creation | User is Viewer role | Upgrade to Member role |
| Credits exhausted mid-campaign | No budget cap on table | Set max_rows on table |
| Integration key rejected | Key was revoked | Generate new key, update integration config |
| Unauthorized data export | Viewer exported sensitive data | Review export audit log |
| Former employee still has access | No offboarding process | Immediate removal on departure |

## Resources

- [Clay Plans & Billing](https://university.clay.com/docs/plans-and-billing)
- [Clay Community](https://community.clay.com)

## Next Steps

For migration strategies, see `clay-migration-deep-dive`.
