# Apollo Upgrade Migration - Implementation Guide

> Full implementation details and code examples for the `apollo-upgrade-migration` skill.

# Apollo Upgrade Migration

## Overview
Plan and execute safe upgrades for Apollo.io API integrations, handling breaking changes and deprecated endpoints.

## Pre-Upgrade Assessment

### Check Current API Usage
```bash
# Find all Apollo API calls in codebase
grep -r "api.apollo.io" --include="*.ts" --include="*.js" -l

# List unique endpoints used
grep -roh "api.apollo.io/v[0-9]*/[a-z_/]*" --include="*.ts" --include="*.js" | sort -u

# Check for deprecated patterns
grep -rn "deprecated\|legacy" --include="*.ts" src/lib/apollo/
```

### Audit Script
```typescript
// scripts/apollo-audit.ts
import { readFileSync, readdirSync } from 'fs';
import { join } from 'path';

interface AuditResult {
  file: string;
  line: number;
  pattern: string;
  severity: 'warning' | 'error';
  message: string;
}

const DEPRECATED_PATTERNS = [
  {
    pattern: /\/v1\/contacts\//,
    message: 'Use /v1/people/ instead of /v1/contacts/',
    severity: 'error' as const,
  },
  {
    pattern: /organization_name/,
    message: 'Use q_organization_domains instead of organization_name',
    severity: 'warning' as const,
  },
  {
    pattern: /\.then\s*\(/,
    message: 'Consider using async/await for cleaner code',
    severity: 'warning' as const,
  },
];

function auditFile(filePath: string): AuditResult[] {
  const content = readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');
  const results: AuditResult[] = [];

  lines.forEach((line, index) => {
    for (const { pattern, message, severity } of DEPRECATED_PATTERNS) {
      if (pattern.test(line)) {
        results.push({
          file: filePath,
          line: index + 1,
          pattern: pattern.source,
          severity,
          message,
        });
      }
    }
  });

  return results;
}

function auditDirectory(dir: string): AuditResult[] {
  const results: AuditResult[] = [];

  function walkDir(currentDir: string) {
    const files = readdirSync(currentDir, { withFileTypes: true });
    for (const file of files) {
      const path = join(currentDir, file.name);
      if (file.isDirectory() && !file.name.includes('node_modules')) {
        walkDir(path);
      } else if (file.name.endsWith('.ts') || file.name.endsWith('.js')) {
        results.push(...auditFile(path));
      }
    }
  }

  walkDir(dir);
  return results;
}

// Run audit
const results = auditDirectory('./src');
console.log('Apollo API Audit Results:\n');

for (const result of results) {
  const icon = result.severity === 'error' ? '[ERR]' : '[WRN]';
  console.log(`${icon} ${result.file}:${result.line}`);
  console.log(`     ${result.message}\n`);
}

console.log(`Total: ${results.length} issues found`);
```

## Migration Steps

### Step 1: Create Compatibility Layer
```typescript
// src/lib/apollo/compat.ts
import { apollo } from './client';

/**
 * Compatibility layer for deprecated API patterns.
 * Remove after all code is updated.
 * @deprecated Use new API directly
 */
export const apolloCompat = {
  /**
   * @deprecated Use apollo.searchPeople()
   */
  async searchContacts(params: any) {
    console.warn('searchContacts is deprecated, use searchPeople');
    return apollo.searchPeople(params);
  },

  /**
   * @deprecated Use q_organization_domains parameter
   */
  async searchByCompanyName(companyName: string) {
    console.warn('searchByCompanyName is deprecated');
    // Try to find domain from company name
    const orgSearch = await apollo.searchOrganizations({
      q_organization_name: companyName,
      per_page: 1,
    });

    if (orgSearch.organizations.length === 0) {
      throw new Error(`Company not found: ${companyName}`);
    }

    const domain = orgSearch.organizations[0].primary_domain;
    return apollo.searchPeople({
      q_organization_domains: [domain],
    });
  },
};
```

### Step 2: Update Imports Gradually
```typescript
// Before migration
import { searchContacts } from '../lib/apollo/legacy';

// During migration (use compat layer)
import { apolloCompat } from '../lib/apollo/compat';
const results = await apolloCompat.searchContacts(params);

// After migration (use new API)
import { apollo } from '../lib/apollo/client';
const results = await apollo.searchPeople(params);
```

### Step 3: Feature Flag for New API
```typescript
// src/lib/apollo/feature-flags.ts
export const USE_NEW_APOLLO_API = process.env.APOLLO_USE_NEW_API === 'true';

// src/services/leads.ts
import { apollo } from '../lib/apollo/client';
import { apolloCompat } from '../lib/apollo/compat';
import { USE_NEW_APOLLO_API } from '../lib/apollo/feature-flags';

export async function searchLeads(criteria: SearchCriteria) {
  if (USE_NEW_APOLLO_API) {
    return apollo.searchPeople({
      q_organization_domains: criteria.domains,
      person_titles: criteria.titles,
    });
  } else {
    // Legacy path
    return apolloCompat.searchContacts({
      organization_domains: criteria.domains,
      titles: criteria.titles,
    });
  }
}
```

### Step 4: Parallel Testing
```typescript
// scripts/compare-api-results.ts
import { apollo } from '../src/lib/apollo/client';
import { apolloCompat } from '../src/lib/apollo/compat';

async function compareResults() {
  const testCases = [
    { domains: ['stripe.com'], titles: ['Engineer'] },
    { domains: ['apollo.io'], titles: ['Sales'] },
  ];

  for (const testCase of testCases) {
    console.log(`\nTesting: ${JSON.stringify(testCase)}`);

    // New API
    const newResult = await apollo.searchPeople({
      q_organization_domains: testCase.domains,
      person_titles: testCase.titles,
      per_page: 10,
    });

    // Legacy API (through compat)
    const legacyResult = await apolloCompat.searchContacts({
      organization_domains: testCase.domains,
      titles: testCase.titles,
      per_page: 10,
    });

    // Compare
    const newCount = newResult.people.length;
    const legacyCount = legacyResult.people.length;

    console.log(`  New API: ${newCount} results`);
    console.log(`  Legacy:  ${legacyCount} results`);
    console.log(`  Match:   ${newCount === legacyCount ? 'YES' : 'NO'}`);
  }
}

compareResults().catch(console.error);
```

## Rollout Strategy

### Phase 1: Canary (1%)
```yaml
# kubernetes/apollo-canary.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: apollo-config-canary
data:
  APOLLO_USE_NEW_API: "true"
---
# Deploy to 1% of traffic
```

### Phase 2: Gradual Rollout
```typescript
// Gradual rollout based on user ID
function shouldUseNewApi(userId: string): boolean {
  const rolloutPercentage = parseInt(process.env.APOLLO_NEW_API_ROLLOUT || '0');
  const hash = hashCode(userId) % 100;
  return hash < rolloutPercentage;
}

function hashCode(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}
```

### Phase 3: Full Migration
```bash
# After successful canary
export APOLLO_USE_NEW_API=true

# Remove compat layer
rm src/lib/apollo/compat.ts

# Update all imports
find src -name "*.ts" -exec sed -i 's/apolloCompat/apollo/g' {} \;
```

## Post-Migration Cleanup

```bash
# Remove deprecated code
grep -rl "deprecated" --include="*.ts" src/lib/apollo/ | xargs rm -v

# Update documentation
# Remove compat layer documentation
# Update API examples to new format

# Final audit
npm run audit:apollo
```

## Rollback Procedure

```bash
# If issues detected, rollback immediately
export APOLLO_USE_NEW_API=false

# Or rollback deployment
kubectl rollout undo deployment/api-server
```

## Output
- Pre-upgrade audit results
- Compatibility layer for gradual migration
- Feature flag controlled rollout
- Parallel testing verification
- Cleanup procedures

## Error Handling
| Issue | Resolution |
|-------|------------|
| Audit finds errors | Fix before proceeding |
| Compat layer fails | Check mapping logic |
| Results differ | Investigate API changes |
| Canary issues | Immediate rollback |

## Resources
- [Apollo API Changelog](https://apolloio.github.io/apollo-api-docs/#changelog)
- [Apollo Migration Guides](https://knowledge.apollo.io/)
- [Feature Flag Best Practices](https://martinfowler.com/articles/feature-toggles.html)

## Next Steps
Proceed to `apollo-ci-integration` for CI/CD setup.
