---
name: clay-migration-deep-dive
description: |
  Migrate to Clay from other enrichment tools or consolidate multiple data sources into Clay.
  Use when migrating from ZoomInfo, Apollo, Clearbit, or custom enrichment scripts to Clay,
  or consolidating fragmented enrichment workflows.
  Trigger with phrases like "migrate to clay", "clay migration", "switch to clay",
  "replace zoominfo with clay", "consolidate enrichment tools".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, migration]

---
# Clay Migration Deep Dive

## Overview

Comprehensive guide for migrating from standalone enrichment tools (ZoomInfo, Apollo, Clearbit, Lusha) to Clay, or consolidating multiple tools into a single Clay-based pipeline. Clay replaces the need for individual provider subscriptions by aggregating 150+ providers into waterfall enrichment workflows.

## Prerequisites

- Current enrichment tool subscription(s) with data export capability
- Clay account on Growth or Enterprise plan
- Understanding of current enrichment volume and costs
- CRM with existing enriched data

## Migration Types

| Migration | Complexity | Duration | Risk |
|-----------|-----------|----------|------|
| Single provider -> Clay | Low | 1-2 weeks | Low |
| Multiple providers -> Clay | Medium | 2-4 weeks | Medium |
| Custom scripts -> Clay | Medium | 2-4 weeks | Medium |
| Full GTM stack migration | High | 1-2 months | High |

## Instructions

### Step 1: Audit Current Enrichment Stack (Week 1)

```typescript
// migration/audit.ts — document your current enrichment setup
interface EnrichmentAudit {
  provider: string;
  monthlyVolume: number;
  monthlyCoost: number;
  dataFields: string[];
  hitRate: number;           // % of lookups that return data
  integrationMethod: string; // API, CSV, Zapier, native CRM
  canExportHistory: boolean;
}

const currentStack: EnrichmentAudit[] = [
  {
    provider: 'ZoomInfo',
    monthlyVolume: 5000,
    monthlyCoost: 15000,  // ZoomInfo is expensive
    dataFields: ['email', 'phone', 'title', 'company', 'revenue'],
    hitRate: 75,
    integrationMethod: 'API + Salesforce native',
    canExportHistory: true,
  },
  {
    provider: 'Apollo.io',
    monthlyVolume: 3000,
    monthlyCoost: 400,
    dataFields: ['email', 'title', 'company', 'linkedin'],
    hitRate: 65,
    integrationMethod: 'API',
    canExportHistory: true,
  },
  {
    provider: 'Custom Python scripts',
    monthlyVolume: 1000,
    monthlyCoost: 0,  // Just developer time
    dataFields: ['email', 'company_data'],
    hitRate: 40,
    integrationMethod: 'Cron job + DB',
    canExportHistory: true,
  },
];

function generateMigrationReport(stack: EnrichmentAudit[]): void {
  const totalCost = stack.reduce((s, p) => s + p.monthlyCoost, 0);
  const totalVolume = stack.reduce((s, p) => s + p.monthlyVolume, 0);
  console.log(`Current stack: ${stack.length} providers`);
  console.log(`Total monthly cost: $${totalCost}`);
  console.log(`Total monthly volume: ${totalVolume} lookups`);
  console.log(`Average hit rate: ${(stack.reduce((s, p) => s + p.hitRate, 0) / stack.length).toFixed(0)}%`);
  console.log(`\nClay equivalent (Growth plan): $495/mo + provider API keys`);
}
```

### Step 2: Map Fields to Clay Columns (Week 1)

```yaml
# migration/field-mapping.yaml
field_mapping:
  # Your current field -> Clay enrichment column
  email: "Work Email (Waterfall: Apollo > Hunter)"
  phone: "Phone Number (Apollo)"
  job_title: "Job Title (Apollo/PDL)"
  company_name: "Company Name (Clearbit)"
  company_revenue: "Revenue (Clearbit)"
  employee_count: "Employee Count (Clearbit)"
  industry: "Industry (Clearbit)"
  tech_stack: "Technologies (BuiltWith via Claygent)"
  linkedin: "LinkedIn URL (Apollo)"

  # Fields that don't have direct Clay equivalents:
  intent_signals: "Use Clay's Web Intent feature (Growth plan)"
  custom_research: "Claygent AI research column"
```

### Step 3: Parallel Run (Week 2-3)

Run Clay alongside your existing tools to validate data quality:

```typescript
// migration/parallel-run.ts
interface ComparisonResult {
  field: string;
  oldValue: string | null;
  clayValue: string | null;
  match: boolean;
}

async function compareEnrichment(
  email: string,
  oldData: Record<string, unknown>,
  clayData: Record<string, unknown>,
): Promise<ComparisonResult[]> {
  const fieldsToCompare = ['company_name', 'job_title', 'employee_count', 'industry'];

  return fieldsToCompare.map(field => ({
    field,
    oldValue: (oldData[field] as string) || null,
    clayValue: (clayData[field] as string) || null,
    match: String(oldData[field]).toLowerCase() === String(clayData[field]).toLowerCase(),
  }));
}

// Run on a sample of 500 contacts from your CRM
// Compare Clay's enrichment with your current provider's data
// Target: Clay should match or exceed current hit rates
```

### Step 4: Configure Clay Table to Replace Current Stack (Week 3)

```yaml
# Clay table configuration to replace multi-provider stack
replacement_table:
  name: "Outbound Leads (Migrated)"
  sources:
    - webhook (replaces API calls to ZoomInfo/Apollo)
    - CRM import (replaces native CRM enrichment)
    - CSV upload (replaces manual processes)

  enrichment_columns:
    1_company_lookup:
      provider: clearbit
      replaces: "ZoomInfo company data"
      own_api_key: true  # 0 Clay credits

    2_email_waterfall:
      providers: [apollo, hunter]
      replaces: "ZoomInfo email + Apollo email"
      own_api_keys: true

    3_person_enrichment:
      provider: apollo
      replaces: "Apollo person data"
      own_api_key: true

    4_ai_research:
      type: claygent
      replaces: "Custom Python research scripts"
      prompt: "Research {{Company Name}} for recent news and tech stack"

    5_icp_scoring:
      type: formula
      replaces: "Custom scoring in Python/SQL"
```

### Step 5: Gradual Traffic Migration (Week 4)

```typescript
// migration/traffic-shift.ts
interface MigrationConfig {
  clayPercentage: number;   // 0-100, gradually increase
  legacyEnabled: boolean;
}

class MigrationRouter {
  constructor(private config: MigrationConfig) {}

  shouldUseClay(): boolean {
    return Math.random() * 100 < this.config.clayPercentage;
  }

  async enrichLead(lead: Record<string, unknown>): Promise<Record<string, unknown>> {
    if (this.shouldUseClay()) {
      return this.enrichViaClay(lead);
    }
    return this.enrichViaLegacy(lead);
  }
}

// Migration schedule:
// Week 4, Day 1: 10% to Clay, 90% legacy
// Week 4, Day 3: 25% to Clay, 75% legacy
// Week 4, Day 5: 50% to Clay, 50% legacy
// Week 5, Day 1: 100% to Clay, legacy disabled
```

### Step 6: Cancel Legacy Subscriptions

After full migration and 2-week monitoring:

- [ ] Verify Clay hit rates match or exceed legacy providers
- [ ] Confirm CRM sync working correctly
- [ ] Export final data from legacy tools as backup
- [ ] Cancel ZoomInfo/Apollo/Clearbit subscriptions
- [ ] Remove legacy API keys from application code
- [ ] Document Clay configuration for team

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Lower hit rate on Clay | Different provider coverage | Adjust waterfall order, add providers |
| Missing fields | Clay uses different field names | Update field mapping |
| Data format mismatch | Different date/number formats | Add transformation in webhook handler |
| CRM duplicates during parallel | Both systems writing | Deduplicate on email in CRM |

## Resources

- [Clay Integrations Directory](https://www.clay.com/integrations)
- [Clay University -- Sources](https://university.clay.com/docs/sources)
- [Clay University -- CSV Import](https://university.clay.com/docs/csv-import-overview)

## Next Steps

For advanced troubleshooting, see `clay-advanced-troubleshooting`.
