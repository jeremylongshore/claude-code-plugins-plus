# Upgrade Verification & Rollback

## Upgrade Verification Script

Run this after upgrading to confirm imports resolve, the client connects, and a
crawler instantiates cleanly. It exits non-zero if any check fails, so it can be
wired into CI as a post-upgrade gate.

```typescript
// verify-upgrade.ts — run after upgrading
import { Actor } from 'apify';
import { CheerioCrawler, log } from 'crawlee';
import { ApifyClient } from 'apify-client';

async function verifyUpgrade() {
  const checks: { name: string; pass: boolean; error?: string }[] = [];

  // Check 1: Imports work
  checks.push({ name: 'Actor import', pass: typeof Actor.init === 'function' });
  checks.push({ name: 'CheerioCrawler import', pass: typeof CheerioCrawler === 'function' });
  checks.push({ name: 'ApifyClient import', pass: typeof ApifyClient === 'function' });

  // Check 2: Client connects
  try {
    const client = new ApifyClient({ token: process.env.APIFY_TOKEN });
    const user = await client.user().get();
    checks.push({ name: 'API connection', pass: !!user.username });
  } catch (err) {
    checks.push({ name: 'API connection', pass: false, error: (err as Error).message });
  }

  // Check 3: Crawler instantiates
  try {
    const crawler = new CheerioCrawler({
      requestHandler: async () => {},
    });
    checks.push({ name: 'Crawler instantiation', pass: true });
  } catch (err) {
    checks.push({ name: 'Crawler instantiation', pass: false, error: (err as Error).message });
  }

  // Report
  console.log('\n=== Upgrade Verification ===');
  for (const check of checks) {
    const status = check.pass ? 'PASS' : 'FAIL';
    console.log(`  [${status}] ${check.name}${check.error ? ` — ${check.error}` : ''}`);
  }

  const allPassed = checks.every(c => c.pass);
  console.log(`\n${allPassed ? 'All checks passed.' : 'Some checks failed!'}`);
  process.exit(allPassed ? 0 : 1);
}

verifyUpgrade();
```

## Rollback Procedure

```bash
# Revert to previous versions
npm install apify@3.1.0 crawlee@3.10.0 apify-client@2.9.0 --save-exact

# Or restore from lock file
git checkout main -- package-lock.json
npm ci

# On the platform: roll back Actor build
# Console > Actor > Builds > select previous build > Set as default
```
