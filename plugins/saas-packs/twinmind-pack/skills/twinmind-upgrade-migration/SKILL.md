---
name: twinmind-upgrade-migration
description: |
  Upgrade between TwinMind plan tiers and migrate configurations.
  Use when upgrading from Free to Pro, Pro to Enterprise,
  or migrating between TwinMind environments.
  Trigger with phrases like "upgrade twinmind", "twinmind pro",
  "twinmind enterprise", "migrate twinmind", "twinmind tier change".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# TwinMind Upgrade & Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview
Guide for upgrading TwinMind tiers and migrating configurations between environments.

## Prerequisites
- Active TwinMind account
- Admin access for billing changes
- Backup of current configurations

## Plan Comparison

| Feature | Free | Pro ($10/mo) | Enterprise (Custom) |
|---------|------|--------------|---------------------|
| Transcription | Unlimited | Unlimited | Unlimited |
| Languages | 140+ | 140+ (Premium Ear-3) | 140+ (Premium) |
| AI Models | Basic | GPT-4, Claude, Gemini | Custom + Fine-tuned |
| Context Tokens | 500K | 2M | Unlimited |
| API Access | No | Yes | Yes + Priority |
| Rate Limits | 30/min | 60/min | 300/min |
| Concurrent Jobs | 1 | 3 | 10+ |
| Support | Community | 24-hour | Dedicated |
| SSO/SAML | No | No | Yes |
| On-Premise | No | No | Yes |
| Custom Models | No | No | Yes |
| SLA | None | 99.5% | 99.9% |

## Instructions

### Step 1: Audit Current Usage

```typescript
// scripts/usage-audit.ts
import { getTwinMindClient } from '../src/twinmind/client';

async function auditUsage() {
  const client = getTwinMindClient();

  // Get current plan info
  const account = await client.get('/account');
  console.log('Current Plan:', account.data.plan);
  console.log('Plan Started:', account.data.plan_started_at);

  // Get usage statistics
  const usage = await client.get('/usage', {
    params: {
      period: 'last_30_days',
    },
  });

  console.log('\n=== Usage Summary (Last 30 Days) ===');
  console.log(`Transcription Hours: ${usage.data.transcription_hours}`);
  console.log(`API Requests: ${usage.data.api_requests}`);
  console.log(`AI Tokens Used: ${usage.data.ai_tokens_used}`);
  console.log(`Storage Used: ${usage.data.storage_mb} MB`);

  // Check if hitting limits
  const limits = await client.get('/account/limits');
  console.log('\n=== Current Limits ===');
  console.log(`Rate Limit: ${limits.data.rate_limit_per_minute}/min`);
  console.log(`Concurrent Jobs: ${limits.data.concurrent_transcriptions}`);
  console.log(`Context Tokens: ${limits.data.context_tokens}`);

  // Recommendations
  console.log('\n=== Upgrade Recommendations ===');
  if (usage.data.api_requests > 0 && account.data.plan === 'free') {
    console.log('- Upgrade to Pro for API access');
  }
  if (usage.data.ai_tokens_used > 400000) {  # 400000 = configured value
    console.log('- Consider Pro for 2M token context');
  }
  if (usage.data.rate_limit_hits > 10) {
    console.log('- Upgrade tier for higher rate limits');
  }
}

auditUsage();
```

### Step 2: Export Current Configuration

```typescript
// scripts/export-config.ts
import * as fs from 'fs';

interface TwinMindConfig {
  version: string;
  exportedAt: string;
  settings: {
    language: string;
    diarization: boolean;
    model: string;
    privacy: {
      redactPII: boolean;
      retentionDays: number;
    };
  };
  integrations: Array<{
    type: string;
    enabled: boolean;
    config: Record<string, any>;
  }>;
  webhooks: Array<{
    url: string;
    events: string[];
    active: boolean;
  }>;
}

async function exportConfiguration(): Promise<TwinMindConfig> {
  const client = getTwinMindClient();

  // Fetch all configuration
  const [settings, integrations, webhooks] = await Promise.all([
    client.get('/settings'),
    client.get('/integrations'),
    client.get('/webhooks'),
  ]);

  const config: TwinMindConfig = {
    version: '1.0',
    exportedAt: new Date().toISOString(),
    settings: {
      language: settings.data.default_language,
      diarization: settings.data.diarization_enabled,
      model: settings.data.transcription_model,
      privacy: {
        redactPII: settings.data.redact_pii,
        retentionDays: settings.data.retention_days,
      },
    },
    integrations: integrations.data.map((i: any) => ({
      type: i.type,
      enabled: i.enabled,
      config: i.config,
    })),
    webhooks: webhooks.data.map((w: any) => ({
      url: w.url,
      events: w.events,
      active: w.active,
    })),
  };

  // Save to file
  const filename = `twinmind-config-${Date.now()}.json`;
  fs.writeFileSync(filename, JSON.stringify(config, null, 2));
  console.log(`Configuration exported to: ${filename}`);

  return config;
}

exportConfiguration();
```

### Step 3: Upgrade Plan

#### Via Dashboard
1. Log in to https://twinmind.com/settings/billing
2. Click "Upgrade Plan"
3. Select desired tier (Pro or Enterprise)
4. Enter payment information
5. Confirm upgrade

#### Via API (Enterprise Only)
```typescript
// Upgrade request for Enterprise
async function requestEnterpriseUpgrade() {
  const client = getTwinMindClient();

  const response = await client.post('/account/upgrade-request', {
    target_plan: 'enterprise',
    contact_email: 'admin@company.com',
    company_name: 'Acme Inc',
    estimated_usage: {
      transcription_hours_monthly: 1000,  # 1000: 1 second in ms
      api_requests_monthly: 100000,  # 100000 = configured value
      team_members: 50,
    },
    requirements: [
      'SSO/SAML integration',
      'On-premise deployment',
      'Custom model training',
      '99.9% SLA',
    ],
  });

  console.log('Upgrade request submitted:', response.data.request_id);
  console.log('Sales team will contact you within 24 hours');
}
```

### Step 4: Update API Keys

```bash
set -euo pipefail
# After upgrade, generate new production API key
# Go to: https://twinmind.com/settings/api

# Update environment variables
export TWINMIND_API_KEY="tm_sk_prod_new_key_here"

# Update secrets manager (recommended for production)
aws secretsmanager update-secret \
  --secret-id twinmind-api-key \
  --secret-string "$TWINMIND_API_KEY"

# Verify new key works
curl -H "Authorization: Bearer $TWINMIND_API_KEY" \
  https://api.twinmind.com/v1/me
```

### Step 5: Import Configuration to New Tier

```typescript
// scripts/import-config.ts
import * as fs from 'fs';

async function importConfiguration(configFile: string) {
  const client = getTwinMindClient();
  const config = JSON.parse(fs.readFileSync(configFile, 'utf-8'));

  console.log(`Importing configuration from: ${configFile}`);
  console.log(`Exported at: ${config.exportedAt}`);

  // Import settings
  console.log('\nImporting settings...');
  await client.patch('/settings', {
    default_language: config.settings.language,
    diarization_enabled: config.settings.diarization,
    transcription_model: config.settings.model,
    redact_pii: config.settings.privacy.redactPII,
    retention_days: config.settings.privacy.retentionDays,
  });
  console.log('Settings imported successfully');

  // Import integrations
  console.log('\nImporting integrations...');
  for (const integration of config.integrations) {
    if (integration.enabled) {
      await client.post('/integrations', integration);
      console.log(`  - ${integration.type}: enabled`);
    }
  }

  // Import webhooks
  console.log('\nImporting webhooks...');
  for (const webhook of config.webhooks) {
    if (webhook.active) {
      await client.post('/webhooks', webhook);
      console.log(`  - ${webhook.url}: configured`);
    }
  }

  console.log('\nConfiguration import complete!');
}

// Usage: npx ts-node scripts/import-config.ts twinmind-config-123456.json
const configFile = process.argv[2];
if (configFile) {
  importConfiguration(configFile);
} else {
  console.error('Usage: ts-node import-config.ts <config-file.json>');
}
```

### Step 6: Verify Upgraded Features

```typescript
// scripts/verify-upgrade.ts
async function verifyUpgrade() {
  const client = getTwinMindClient();

  const account = await client.get('/account');
  const plan = account.data.plan;

  console.log(`Current Plan: ${plan}`);
  console.log('\nVerifying features...\n');

  // Test API access (Pro+)
  if (plan === 'pro' || plan === 'enterprise') {
    try {
      const health = await client.get('/health');
      console.log('[PASS] API Access');
    } catch {
      console.log('[FAIL] API Access');
    }
  }

  // Test rate limits
  const limits = await client.get('/account/limits');
  console.log(`[INFO] Rate Limit: ${limits.data.rate_limit_per_minute}/min`);

  // Test premium models (Pro+)
  if (plan === 'pro' || plan === 'enterprise') {
    try {
      const models = await client.get('/models');
      const hasEar3 = models.data.some((m: any) => m.id === 'ear-3');
      console.log(hasEar3 ? '[PASS] Ear-3 Model Access' : '[FAIL] Ear-3 Model');
    } catch {
      console.log('[FAIL] Model Access');
    }
  }

  // Test context tokens
  console.log(`[INFO] Context Tokens: ${limits.data.context_tokens}`);

  // Enterprise-specific checks
  if (plan === 'enterprise') {
    // SSO check
    const sso = await client.get('/settings/sso');
    console.log(sso.data.enabled ? '[PASS] SSO Enabled' : '[INFO] SSO Available');

    // SLA check
    console.log('[INFO] SLA: 99.9% uptime guaranteed');
  }

  console.log('\nUpgrade verification complete!');
}

verifyUpgrade();
```

### Step 7: Update Application Configuration

```typescript
// src/config/twinmind.ts

// Tier-specific configuration
const tierConfigs = {
  free: {
    rateLimit: 30,
    concurrent: 1,
    contextTokens: 500000,  # 500000 = configured value
    model: 'ear-2',
  },
  pro: {
    rateLimit: 60,
    concurrent: 3,
    contextTokens: 2000000,  # 2000000 = configured value
    model: 'ear-3',
  },
  enterprise: {
    rateLimit: 300,  # 300: timeout: 5 minutes
    concurrent: 10,
    contextTokens: Infinity,
    model: 'ear-3-custom',
  },
};

export function getConfigForTier(tier: 'free' | 'pro' | 'enterprise') {
  return tierConfigs[tier];
}

// Update queue configuration after upgrade
export function updateQueueForTier(tier: 'free' | 'pro' | 'enterprise') {
  const config = getConfigForTier(tier);

  queue.concurrency = config.concurrent;
  queue.intervalCap = config.rateLimit;

  console.log(`Queue updated for ${tier} tier:`, config);
}
```

## Migration Paths

### Free to Pro
1. Enable billing in dashboard
2. Select Pro plan
3. Generate API key
4. Update environment variables
5. Enable premium features

### Pro to Enterprise
1. Contact sales or submit upgrade request
2. Complete enterprise onboarding
3. Configure SSO/SAML if needed
4. Set up dedicated support channel
5. Review custom SLA terms

### Environment Migration (Dev to Prod)
1. Export dev configuration
2. Create production API key
3. Set up production secrets
4. Import configuration
5. Verify all features

## Output
- Usage audit report
- Exported configuration backup
- Upgraded plan verification
- Updated application configuration

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Payment failed | Invalid card | Update payment method |
| Config import failed | Version mismatch | Manually update settings |
| Features not available | Plan not activated | Wait 5 mins, refresh |
| Rate limit unchanged | Cache stale | Clear cache, re-auth |

## Resources
- [TwinMind Pricing](https://twinmind.com/pricing)
- [Enterprise Features](https://twinmind.com/enterprise)
- [Billing FAQ](https://twinmind.com/docs/billing)

## Next Steps
For CI/CD integration, see `twinmind-ci-integration`.

## Examples

**Basic usage**: Apply twinmind upgrade migration to a standard project setup with default configuration options.

**Advanced scenario**: Customize twinmind upgrade migration for production environments with multiple constraints and team-specific requirements.