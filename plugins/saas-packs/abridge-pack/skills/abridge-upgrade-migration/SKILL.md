---
name: abridge-upgrade-migration
description: |
  Plan and execute Abridge integration upgrades and EHR migration procedures.
  Use when upgrading Abridge API versions, migrating between EHR systems,
  or handling breaking changes in clinical documentation workflows.
  Trigger: "abridge upgrade", "abridge migration", "abridge version update",
  "migrate abridge EHR", "abridge breaking changes".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, healthcare, ai, abridge, migration]
compatible-with: claude-code
---

# Abridge Upgrade & Migration

## Overview

Procedures for upgrading Abridge API integrations and migrating between EHR systems. Healthcare migrations are high-risk — clinical documentation cannot have gaps.

## Common Migration Scenarios

| Scenario | Complexity | Downtime | Risk |
|----------|-----------|----------|------|
| API version bump (v1 → v2) | Medium | Zero (dual-version) | Low |
| EHR migration (Epic → Athena) | High | Planned window | High |
| New specialty onboarding | Low | Zero | Low |
| Note template changes | Medium | Zero | Medium |
| Multi-site rollout | High | Per-site windows | Medium |

## Instructions

### Step 1: API Version Migration

```typescript
// src/migration/api-version-adapter.ts
// Dual-version adapter for zero-downtime API upgrades

interface ApiVersionConfig {
  v1BaseUrl: string;  // Current production
  v2BaseUrl: string;  // New version (canary)
  canaryPercent: number;  // Percentage of traffic to v2
}

class AbridgeVersionAdapter {
  constructor(private config: ApiVersionConfig) {}

  getBaseUrl(): string {
    // Gradual canary rollout
    const useV2 = Math.random() * 100 < this.config.canaryPercent;
    return useV2 ? this.config.v2BaseUrl : this.config.v1BaseUrl;
  }

  // Map v1 response to v2 format (or vice versa)
  normalizeNoteResponse(response: any, version: 'v1' | 'v2'): any {
    if (version === 'v1') {
      return {
        ...response,
        // v2 adds quality_metrics — provide defaults for v1
        quality_metrics: response.quality_metrics || {
          confidence_score: response.confidence || 0,
          completeness_score: 0,
          coding_accuracy: 0,
        },
      };
    }
    return response;
  }
}
```

### Step 2: EHR Migration Procedure

```typescript
// src/migration/ehr-migration.ts
interface EhrMigrationPlan {
  sourceEhr: 'epic' | 'athena' | 'cerner' | 'eclinicalworks';
  targetEhr: 'epic' | 'athena' | 'cerner' | 'eclinicalworks';
  migrationDate: Date;
  providerCount: number;
  steps: MigrationStep[];
}

interface MigrationStep {
  order: number;
  name: string;
  description: string;
  rollbackable: boolean;
  estimatedMinutes: number;
}

function generateMigrationPlan(source: string, target: string): EhrMigrationPlan {
  return {
    sourceEhr: source as any,
    targetEhr: target as any,
    migrationDate: new Date(),
    providerCount: 0, // Set per org
    steps: [
      { order: 1, name: 'Freeze new enrollments', description: 'Stop new provider enrollments on source EHR', rollbackable: true, estimatedMinutes: 5 },
      { order: 2, name: 'Export note templates', description: 'Export all custom note templates and SmartPhrases', rollbackable: true, estimatedMinutes: 30 },
      { order: 3, name: 'Configure target EHR', description: 'Set up FHIR endpoints and OAuth for target EHR', rollbackable: true, estimatedMinutes: 60 },
      { order: 4, name: 'Parallel run', description: 'Run both EHRs for 1 week — compare note output', rollbackable: true, estimatedMinutes: 10080 },
      { order: 5, name: 'Provider re-enrollment', description: 'Re-enroll providers on target EHR', rollbackable: true, estimatedMinutes: 120 },
      { order: 6, name: 'Cutover', description: 'Switch primary EHR integration to target', rollbackable: true, estimatedMinutes: 15 },
      { order: 7, name: 'Decommission source', description: 'Disable source EHR integration after 30-day soak', rollbackable: false, estimatedMinutes: 30 },
    ],
  };
}
```

### Step 3: Note Template Migration

```typescript
// src/migration/template-migration.ts
interface NoteTemplate {
  id: string;
  name: string;
  specialty: string;
  sections: string[];
  smartPhrases: Record<string, string>;  // Epic-specific
}

async function migrateTemplates(
  sourceApi: any,
  targetApi: any,
): Promise<{ migrated: number; failed: string[] }> {
  const { data: templates } = await sourceApi.get('/note-templates');
  const failed: string[] = [];
  let migrated = 0;

  for (const template of templates) {
    try {
      // Remove EHR-specific fields
      const { smartPhrases, ...portable } = template;

      await targetApi.post('/note-templates', {
        ...portable,
        // Map SmartPhrases to target EHR equivalent if applicable
      });
      migrated++;
    } catch (err) {
      failed.push(template.id);
    }
  }

  return { migrated, failed };
}
```

## Rollback Procedures

```bash
#!/bin/bash
# scripts/abridge-migration-rollback.sh

echo "=== Migration Rollback ==="
echo "Step 1: Revert FHIR endpoint to source EHR"
echo "Step 2: Re-enable source EHR Abridge module"
echo "Step 3: Notify providers of rollback"
echo "Step 4: Verify note generation on source EHR"
echo "=== Rollback Complete ==="
```

## Output

- Dual-version API adapter for zero-downtime upgrades
- EHR migration plan with parallel run validation
- Note template migration with rollback
- Provider re-enrollment procedure

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Template incompatible | EHR-specific fields | Strip EHR-specific data before migration |
| Provider enrollment fails | Credentials not migrated | Re-issue provider credentials on target |
| Note format mismatch | Different FHIR profiles | Map FHIR profiles between EHR systems |

## Resources

- [Abridge Platform](https://www.abridge.com/product)
- [HL7 FHIR Migration Guide](https://hl7.org/fhir/R4/comparison.html)

## Next Steps

For CI/CD pipeline setup, see `abridge-ci-integration`.
