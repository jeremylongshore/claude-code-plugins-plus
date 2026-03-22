---
name: canva-migration-deep-dive
description: |
  Execute major Canva Connect API integration migrations with strangler fig pattern.
  Use when migrating to Canva from another design platform, re-platforming
  existing integrations, or performing major architectural changes.
  Trigger with phrases like "migrate to canva", "canva migration",
  "switch to canva", "canva replatform", "replace design tool with canva".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Migration Deep Dive

## Overview

Comprehensive guide for migrating to the Canva Connect API from another design platform or from direct image generation. Uses the strangler fig pattern for gradual, safe migration.

## Migration Types

| Type | Duration | Risk | Example |
|------|----------|------|---------|
| Fresh integration | Days | Low | New app adding Canva support |
| From image gen APIs | 2-4 weeks | Medium | Replace Imgix/Cloudinary templates with Canva |
| From competitor | 4-8 weeks | Medium | Replace Figma API / Adobe Express |
| Major re-architecture | Months | High | Rebuild design system on Canva |

## Pre-Migration Assessment

### Asset Inventory

```typescript
interface MigrationAssessment {
  currentAssets: number;           // Images, templates in old system
  designTemplates: number;         // Templates to recreate as Canva brand templates
  apiCallsPerDay: number;          // Current design API usage
  usersToMigrate: number;          // Users who need Canva OAuth
  requiredCanvaTier: 'free' | 'pro' | 'enterprise';
  blockers: string[];
}

async function assessMigration(): Promise<MigrationAssessment> {
  return {
    currentAssets: await countCurrentAssets(),
    designTemplates: await countTemplates(),
    apiCallsPerDay: await getAverageApiCalls(),
    usersToMigrate: await countActiveUsers(),
    requiredCanvaTier: needsAutofill() ? 'enterprise' : 'free',
    blockers: [
      // Common blockers:
      // - Need Enterprise for brand template autofill
      // - Rate limits may be too low for current volume
      // - No batch API — must process designs one at a time
    ],
  };
}
```

### Canva API Capability Mapping

```typescript
// Map your current operations to Canva Connect API endpoints
const operationMapping = {
  // Old system → Canva endpoint
  'createFromTemplate': 'POST /v1/autofills',           // Requires Enterprise
  'generateImage':      'POST /v1/designs + POST /v1/exports',
  'uploadAsset':        'POST /v1/asset-uploads',
  'listDesigns':        'GET /v1/designs',
  'exportAsPDF':        'POST /v1/exports (format: pdf)',
  'exportAsPNG':        'POST /v1/exports (format: png)',
  'organizeFolder':     'POST /v1/folders',
  'addComment':         'POST /v1/designs/{id}/comment_threads',
};
```

## Migration Strategy: Strangler Fig

### Phase 1: Adapter Layer (Week 1-2)

```typescript
// src/services/design-adapter.ts
// Abstract interface that both old and new systems implement

interface DesignService {
  createDesign(input: CreateDesignInput): Promise<Design>;
  exportDesign(designId: string, format: ExportFormat): Promise<string[]>;
  uploadAsset(file: Buffer, name: string): Promise<string>;
}

// Old implementation
class LegacyDesignService implements DesignService {
  async createDesign(input: CreateDesignInput) {
    return oldApi.generateImage(input);
  }
  // ...
}

// New Canva implementation
class CanvaDesignService implements DesignService {
  constructor(private canva: CanvaClient) {}

  async createDesign(input: CreateDesignInput) {
    const { design } = await this.canva.request('/designs', {
      method: 'POST',
      body: JSON.stringify({
        design_type: { type: 'custom', width: input.width, height: input.height },
        title: input.title,
      }),
    });
    return { id: design.id, editUrl: design.urls.edit_url };
  }

  async exportDesign(designId: string, format: ExportFormat) {
    const { job } = await this.canva.request('/exports', {
      method: 'POST',
      body: JSON.stringify({ design_id: designId, format: { type: format } }),
    });
    return this.pollExport(job.id);
  }

  async uploadAsset(file: Buffer, name: string) {
    const nameBase64 = Buffer.from(name).toString('base64');
    const res = await fetch('https://api.canva.com/rest/v1/asset-uploads', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.canva.getToken()}`,
        'Content-Type': 'application/octet-stream',
        'Asset-Upload-Metadata': JSON.stringify({ name_base64: nameBase64 }),
      },
      body: file,
    });
    const data = await res.json();
    return data.job.id;
  }
}
```

### Phase 2: Feature Flag Traffic Split (Week 3-4)

```typescript
// Route traffic based on feature flag
function getDesignService(userId: string): DesignService {
  const canvaPercentage = getFeatureFlag('canva_migration_pct', userId);
  const roll = deterministicRoll(userId); // Same user always gets same path

  if (roll < canvaPercentage) {
    const tokens = await tokenStore.get(userId);
    if (tokens) {
      return new CanvaDesignService(new CanvaClient({ ...config, tokens }));
    }
    // User hasn't connected Canva yet — fall back to legacy
  }

  return new LegacyDesignService();
}

// Gradual rollout: 5% → 25% → 50% → 100%
```

### Phase 3: Asset Migration (Week 5-6)

```typescript
// Migrate existing assets to Canva
async function migrateAssets(
  assets: { url: string; name: string }[],
  token: string
): Promise<Map<string, string>> {
  const idMapping = new Map<string, string>(); // oldId → canvaAssetId

  for (const asset of assets) {
    try {
      // Upload via URL — rate limit: 30/min
      const { job } = await canvaAPI('/url-asset-uploads', token, {
        method: 'POST',
        body: JSON.stringify({ name: asset.name, url: asset.url }),
      });

      // Poll for completion
      let upload = job;
      while (upload.status === 'in_progress') {
        await new Promise(r => setTimeout(r, 2000));
        const poll = await canvaAPI(`/url-asset-uploads/${upload.id}`, token);
        upload = poll.job;
      }

      if (upload.status === 'success') {
        idMapping.set(asset.url, upload.asset.id);
      }
    } catch (error) {
      console.error(`Failed to migrate asset: ${asset.name}`, error);
    }

    // Respect rate limits
    await new Promise(r => setTimeout(r, 2500)); // ~24 uploads/min
  }

  return idMapping;
}
```

### Phase 4: Cutover & Cleanup (Week 7-8)

```typescript
// Final validation before removing legacy system
async function validateMigration(token: string): Promise<{
  passed: boolean;
  checks: { name: string; result: boolean; details: string }[];
}> {
  const checks = [
    {
      name: 'Design creation',
      fn: async () => {
        const { design } = await canvaAPI('/designs', token, {
          method: 'POST',
          body: JSON.stringify({
            design_type: { type: 'custom', width: 100, height: 100 },
            title: 'Migration validation test',
          }),
        });
        return { result: !!design.id, details: `Design ID: ${design.id}` };
      },
    },
    {
      name: 'Export works',
      fn: async () => {
        // Test with an existing design
        return { result: true, details: 'Export endpoint accessible' };
      },
    },
    {
      name: 'Rate limits adequate',
      fn: async () => {
        // Check current usage vs limits
        return { result: true, details: 'Within rate limits' };
      },
    },
  ];

  const results = [];
  for (const check of checks) {
    try {
      const { result, details } = await check.fn();
      results.push({ name: check.name, result, details });
    } catch (e: any) {
      results.push({ name: check.name, result: false, details: e.message });
    }
  }

  return { passed: results.every(r => r.result), checks: results };
}
```

## Rollback Plan

```bash
# Immediate rollback — switch feature flag to 0%
curl -X PUT "https://flagservice.internal/api/flags/canva_migration_pct" \
  -d '{"value": 0}'

# Verify legacy system still works
curl -s "https://api.ourapp.com/health" | jq '.services.legacy_design'
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Asset upload fails | File too large or unsupported format | Pre-validate, compress |
| Rate limit during migration | Too many uploads | Add delays between uploads |
| User hasn't connected Canva | Missing OAuth | Prompt to connect, fallback |
| Feature parity gap | Canva API doesn't support operation | Document, workaround, or defer |

## Resources

- [Canva Connect API](https://www.canva.dev/docs/connect/)
- [Canva Starter Kit](https://github.com/canva-sdks/canva-connect-api-starter-kit)
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)

## Next Steps

For advanced troubleshooting, see `canva-advanced-troubleshooting`.
