---
name: clay-upgrade-migration
description: |
  Navigate Clay plan changes, pricing migrations, and feature upgrades.
  Use when upgrading Clay plans, migrating to the 2026 pricing model,
  or adapting integrations to new Clay features.
  Trigger with phrases like "upgrade clay", "clay migration", "clay pricing change",
  "clay plan upgrade", "clay new pricing".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, api, migration]

---
# Clay Upgrade & Migration

## Overview

Guide for navigating Clay plan upgrades and the March 2026 pricing overhaul. Clay restructured from Starter/Explorer/Pro to Launch/Growth tiers, split credits into Data Credits + Actions, and cut data costs 50-90%. This skill covers migration decisions, integration impact, and adaptation strategies.

## Prerequisites

- Active Clay account
- Understanding of current credit consumption
- Access to Clay billing dashboard

## Instructions

### Step 1: Understand the 2026 Pricing Change

**Old Plans (Legacy -- available until April 10, 2026):**

| Plan | Price | Credits | Key Limits |
|------|-------|---------|------------|
| Starter | $149/mo | Limited | No HTTP API, no webhooks |
| Explorer | $349/mo | 25K | 400 records/hour throttle |
| Pro | $800/mo | 50K | HTTP API, webhooks, priority support |

**New Plans (March 2026+):**

| Plan | Price | Data Credits | Actions | Key Features |
|------|-------|-------------|---------|--------------|
| Launch | $185/mo | 2,500 | 15,000 | Phone enrichment, signal tracking |
| Growth | $495/mo | 6,000 | 40,000 | CRM sync, HTTP API, web intent, ads |

**Key changes:**
- Credits split into **Data Credits** (buying enrichment data) and **Actions** (using the platform)
- Data costs cut 50-90% (each enrichment is cheaper)
- No enrichment charges on failed lookups (no data = no charge)
- Credit rollover capped at 2x monthly limit

### Step 2: Audit Your Current Usage

```bash
# Check current plan and credit usage from Clay dashboard
# Navigate to Settings > Plans & Billing
# Record:
# - Current plan tier
# - Monthly credits used (average over 3 months)
# - Which enrichment providers consume most credits
# - Whether you use HTTP API columns
# - Whether you use webhook sources
```

**Decision matrix for migration:**

| If you currently... | Recommended new plan |
|---------------------|---------------------|
| Use < 2,500 data credits/mo | Launch ($185) |
| Need HTTP API columns | Growth ($495) |
| Need CRM sync | Growth ($495) |
| Use webhooks + high volume | Growth ($495) |
| Stay on legacy Explorer | Keep legacy if 400/hr limit works |
| Have Enterprise contract | Contact Clay sales |

### Step 3: Adapt Integration Code for New Credit Model

```typescript
// src/clay/credit-tracker.ts — track new split credit model
interface CreditUsage {
  dataCredits: { used: number; limit: number; rolloverMax: number };
  actions: { used: number; limit: number };
}

class CreditTracker {
  private usage: CreditUsage;

  constructor(plan: 'launch' | 'growth') {
    this.usage = plan === 'launch'
      ? { dataCredits: { used: 0, limit: 2500, rolloverMax: 5000 }, actions: { used: 0, limit: 15000 } }
      : { dataCredits: { used: 0, limit: 6000, rolloverMax: 12000 }, actions: { used: 0, limit: 40000 } };
  }

  recordEnrichment(dataCreditsUsed: number) {
    this.usage.dataCredits.used += dataCreditsUsed;
    this.usage.actions.used += 1; // Each enrichment = 1 action

    if (this.usage.dataCredits.used > this.usage.dataCredits.limit * 0.8) {
      console.warn(`Data credits at ${((this.usage.dataCredits.used / this.usage.dataCredits.limit) * 100).toFixed(0)}% of monthly limit`);
    }
  }

  canAfford(estimatedCredits: number): boolean {
    return (
      this.usage.dataCredits.used + estimatedCredits <= this.usage.dataCredits.limit &&
      this.usage.actions.used + 1 <= this.usage.actions.limit
    );
  }
}
```

### Step 4: Optimize for the New Model

**No-charge on failed lookups** changes the cost equation:

```typescript
// Old model: every enrichment attempt cost credits, even if no data returned
// New model: only charged when data is actually returned

// This makes wider waterfall enrichments cheaper:
// Before: 5-provider waterfall = 5 charges even if only 1 finds data
// After: 5-provider waterfall = 1 charge if only 1 finds data
// Strategy: wider waterfalls are now more cost-effective
```

**Connect your own API keys** for maximum savings:

| Provider | Clay Credits (managed) | Own Key |
|----------|----------------------|---------|
| Apollo | 2 data credits | 0 credits |
| Clearbit | 2-5 data credits | 0 credits |
| Hunter | 2 data credits | 0 credits |
| ZoomInfo | 5-13 data credits | 0 credits |

### Step 5: Migrate Webhook Integrations

If moving from a plan without webhooks to one with them (or vice versa):

```bash
# Test webhook availability on new plan
curl -X POST "$CLAY_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{"migration_test": true, "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}'

# Verify HTTP API columns still work after plan change
# HTTP API columns are only available on Growth plan
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Features disappeared | Downgraded plan | Check feature availability per tier |
| HTTP API columns disabled | Moved to Launch (no HTTP API) | Upgrade to Growth or use webhooks only |
| Higher credit usage than expected | Actions now counted separately | Monitor both Data Credits and Actions |
| Webhook stopped working | Plan change affected access | Verify webhook feature on current plan |

## Resources

- [Clay Pricing Change 2026](https://www.clay.com/pricing)
- [Clay Plans & Billing](https://university.clay.com/docs/plans-and-billing)
- [Clay Community -- Pricing Discussion](https://community.clay.com)

## Next Steps

For CI integration during upgrades, see `clay-ci-integration`.
