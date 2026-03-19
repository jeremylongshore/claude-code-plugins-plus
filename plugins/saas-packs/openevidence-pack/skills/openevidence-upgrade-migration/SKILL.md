---
name: openevidence-upgrade-migration
description: |
  Upgrade OpenEvidence SDK versions and migrate between API versions.
  Use when upgrading SDK, migrating to new API version,
  or planning OpenEvidence version updates.
  Trigger with phrases like "openevidence upgrade", "openevidence migrate",
  "update openevidence sdk", "openevidence new version", "openevidence breaking changes".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenEvidence Upgrade & Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview
Safely upgrade OpenEvidence SDK versions and migrate between API versions with minimal disruption to clinical workflows.

## Prerequisites
- Current OpenEvidence integration running
- Access to staging environment
- Changelog for target version
- Test suite passing

## Version Compatibility Matrix

| SDK Version | API Version | Node.js | Python | Status |
|-------------|-------------|---------|--------|--------|
| 3.x | v3 | 20+ | 3.11+ | Current |
| 2.x | v2 | 18+ | 3.10+ | Maintained |
| 1.x | v1 | 16+ | 3.8+ | Deprecated |

## Instructions

### Step 1: Review Changelog and Breaking Changes
```bash
set -euo pipefail
# Check current version
npm list @openevidence/sdk
# or
pip show openevidence

# Review changelog
# https://docs.openevidence.com/changelog
```

### Step 2: Update Dependencies
```bash
set -euo pipefail
# Node.js - specific version
npm install @openevidence/sdk@3.0.0

# Node.js - latest
npm install @openevidence/sdk@latest

# Python - specific version
pip install openevidence==3.0.0

# Python - latest
pip install --upgrade openevidence
```

### Step 3: Common Migration Patterns

#### SDK v2 to v3 Migration

**Client Initialization Changes:**
```typescript
// v2 (deprecated)
import { OpenEvidence } from '@openevidence/sdk';
const client = new OpenEvidence(process.env.OPENEVIDENCE_API_KEY);

// v3 (current)
import { OpenEvidenceClient } from '@openevidence/sdk';
const client = new OpenEvidenceClient({
  apiKey: process.env.OPENEVIDENCE_API_KEY,
  orgId: process.env.OPENEVIDENCE_ORG_ID, // Now required
});
```

**Query Method Changes:**
```typescript
// v2 (deprecated)
const response = await client.query('What is the treatment for...');

// v3 (current)
const response = await client.query({
  question: 'What is the treatment for...',
  context: {
    specialty: 'internal-medicine',
    urgency: 'routine',
  },
});
```

**Response Structure Changes:**
```typescript
// v2 response
interface V2Response {
  answer: string;
  sources: string[];
}

// v3 response
interface V3Response {
  answer: string;
  citations: Citation[];  // Renamed and expanded
  confidence: number;     // New field
  lastUpdated: string;    // New field
  id: string;             // New field for tracking
}
```

**DeepConsult Changes:**
```typescript
// v2 (synchronous, limited)
const report = await client.research('complex question');

// v3 (async with status polling)
const consultId = await client.deepConsult.create({
  question: 'complex question',
  context: { specialty: 'oncology', researchFocus: 'treatment' },
});

// Poll for completion or use webhooks
const status = await client.deepConsult.status(consultId);
```

### Step 4: Create Migration Adapter
```typescript
// src/migration/openevidence-adapter.ts
// Temporary adapter for gradual migration

import { OpenEvidenceClient } from '@openevidence/sdk';

interface V2QueryResponse {
  answer: string;
  sources: string[];
}

interface V3QueryResponse {
  answer: string;
  citations: { source: string; title: string; year: number }[];
  confidence: number;
}

export class OpenEvidenceMigrationAdapter {
  private client: OpenEvidenceClient;
  private useV3Response: boolean;

  constructor(config: { apiKey: string; orgId: string; useV3Response?: boolean }) {
    this.client = new OpenEvidenceClient({
      apiKey: config.apiKey,
      orgId: config.orgId,
    });
    this.useV3Response = config.useV3Response ?? false;
  }

  // Maintains v2-compatible interface during migration
  async query(
    question: string,
    options?: { specialty?: string }
  ): Promise<V2QueryResponse | V3QueryResponse> {
    const response = await this.client.query({
      question,
      context: {
        specialty: options?.specialty || 'internal-medicine',
        urgency: 'routine',
      },
    });

    // Return v2-compatible response if not ready for v3
    if (!this.useV3Response) {
      return {
        answer: response.answer,
        sources: response.citations.map(c => c.source),
      };
    }

    return response;
  }
}
```

### Step 5: Update Type Definitions
```typescript
// src/types/openevidence.ts
// Update types for v3 API

export interface ClinicalQueryRequest {
  question: string;
  context: ClinicalContext;
  options?: QueryOptions;
}

export interface ClinicalContext {
  specialty: string;
  urgency: 'stat' | 'urgent' | 'routine' | 'research';
  patientAge?: number;
  patientSex?: 'male' | 'female' | 'other';
  relevantConditions?: string[];
  currentMedications?: string[];
}

export interface QueryOptions {
  maxCitations?: number;
  includeGuidelines?: boolean;
  includeDrugInfo?: boolean;
  preferredSources?: string[];
}

export interface Citation {
  source: string;
  title: string;
  authors: string[];
  year: number;
  doi?: string;
  url?: string;
  type?: 'journal' | 'guideline' | 'textbook';
  evidenceLevel?: string;
}

export interface ClinicalQueryResponse {
  id: string;
  answer: string;
  citations: Citation[];
  confidence: number;
  lastUpdated: string;
  deepConsultAvailable: boolean;
}
```

### Step 6: Test Migration
```typescript
// tests/migration/v2-to-v3.test.ts
import { describe, it, expect } from 'vitest';
import { OpenEvidenceMigrationAdapter } from '../../src/migration/openevidence-adapter';

describe('v2 to v3 Migration', () => {
  const adapter = new OpenEvidenceMigrationAdapter({
    apiKey: process.env.OPENEVIDENCE_API_KEY!,
    orgId: process.env.OPENEVIDENCE_ORG_ID!,
    useV3Response: false, // Test v2 compatibility
  });

  it('should return v2-compatible response format', async () => {
    const response = await adapter.query('What is the treatment for hypertension?');

    expect(response).toHaveProperty('answer');
    expect(response).toHaveProperty('sources');
    expect(Array.isArray((response as any).sources)).toBe(true);
  });

  it('should support specialty parameter', async () => {
    const response = await adapter.query(
      'What is the treatment for hypertension?',
      { specialty: 'cardiology' }
    );

    expect(response.answer).toBeDefined();
  });
});
```

### Step 7: Gradual Rollout Strategy
```typescript
// src/config/feature-flags.ts
export const featureFlags = {
  // Start at 0, gradually increase to 100
  openevidence_v3_percentage: parseInt(process.env.OE_V3_PERCENTAGE || '0'),
};

export function shouldUseV3(): boolean {
  return Math.random() * 100 < featureFlags.openevidence_v3_percentage;
}

// Usage in service
async function clinicalQuery(question: string) {
  if (shouldUseV3()) {
    return v3ClinicalQuery(question);
  }
  return v2ClinicalQuery(question);
}
```

## Migration Checklist

- [ ] Review changelog for breaking changes
- [ ] Update SDK version in package.json/requirements.txt
- [ ] Update type definitions
- [ ] Create migration adapter if needed
- [ ] Update error handling for new error types
- [ ] Update tests for new response formats
- [ ] Test in staging environment
- [ ] Plan gradual rollout
- [ ] Monitor for errors during rollout
- [ ] Remove deprecated code after full migration

## Output
- Updated SDK version
- Type definitions aligned with new API
- Migration adapter for gradual transition
- Tests passing with new version

## Error Handling
| Migration Issue | Cause | Solution |
|-----------------|-------|----------|
| Type errors | Changed response format | Update type definitions |
| Auth failures | New required fields | Add orgId to configuration |
| Missing methods | Renamed or removed | Check changelog for replacements |
| Test failures | Changed behavior | Update test expectations |

## Examples

### Complete Migration Script
```bash
#!/bin/bash
set -euo pipefail
# scripts/migrate-openevidence.sh

echo "=== OpenEvidence SDK Migration ==="

# 1. Check current version
echo "Current version:"
npm list @openevidence/sdk

# 2. Backup package-lock.json
cp package-lock.json package-lock.json.backup

# 3. Update SDK
echo "Updating to latest version..."
npm install @openevidence/sdk@latest

# 4. Run type check
echo "Running type check..."
npx tsc --noEmit || {
  echo "Type errors found. Review and fix before continuing."
  exit 1
}

# 5. Run tests
echo "Running tests..."
npm test || {
  echo "Tests failed. Review and fix before continuing."
  exit 1
}

echo "=== Migration Complete ==="
echo "New version:"
npm list @openevidence/sdk
```

## Resources
- [OpenEvidence Changelog](https://docs.openevidence.com/changelog)
- [OpenEvidence Migration Guide](https://docs.openevidence.com/migration)

## Next Steps
For CI/CD integration, see `openevidence-ci-integration`.