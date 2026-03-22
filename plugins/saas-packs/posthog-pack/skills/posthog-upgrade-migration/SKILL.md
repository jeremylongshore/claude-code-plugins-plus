---
name: posthog-upgrade-migration
description: |
  Upgrade posthog-js and posthog-node SDKs with breaking change detection.
  Covers v4 to v5 posthog-node migration (sendFeatureFlags change),
  posthog-js autocapture API changes, and version-specific gotchas.
  Trigger: "upgrade posthog", "posthog breaking changes",
  "update posthog SDK", "posthog version", "posthog migration".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, posthog, api, migration]
---

# PostHog Upgrade & Migration

## Current State

!`npm list posthog-js posthog-node 2>/dev/null | grep posthog || echo 'No PostHog SDK found'`

## Overview

Upgrade posthog-js and posthog-node SDKs safely. Covers version compatibility, breaking changes between major versions (notably the v5 sendFeatureFlags change in posthog-node), and a systematic upgrade procedure.

## Prerequisites

- PostHog SDK currently installed
- Git for branching
- Test suite covering PostHog integration
- Staging environment for validation

## Instructions

### Step 1: Audit Current Versions

```bash
set -euo pipefail
# Check installed versions
echo "=== posthog-js ==="
npm list posthog-js 2>/dev/null || echo "Not installed"
echo "=== posthog-node ==="
npm list posthog-node 2>/dev/null || echo "Not installed"
echo "=== Python posthog ==="
pip3 show posthog 2>/dev/null | grep Version || echo "Not installed"

# Check latest available versions
echo "=== Latest available ==="
npm view posthog-js version 2>/dev/null
npm view posthog-node version 2>/dev/null
```

### Step 2: Review Breaking Changes

**posthog-node v5.x Breaking Changes:**
```typescript
// BREAKING: sendFeatureFlags no longer automatic with local evaluation
// Before v5.5.0: feature flags auto-sent with events when using local evaluation
// After v5.5.0: must explicitly set sendFeatureFlags: true

// Before (implicit, worked in v4.x)
posthog.capture({
  distinctId: 'user-1',
  event: 'page_viewed',
  // Feature flags were automatically included
});

// After (v5.5.0+, explicit required)
posthog.capture({
  distinctId: 'user-1',
  event: 'page_viewed',
  sendFeatureFlags: true, // Must be explicit now
});
```

**posthog-js Recent Changes:**
```typescript
// Autocapture configuration moved to object format
// Before:
posthog.init('phc_...', { autocapture: true });

// Current: Fine-grained autocapture control
posthog.init('phc_...', {
  autocapture: {
    dom_event_allowlist: ['click', 'submit'],
    element_allowlist: ['a', 'button', 'form', 'input'],
    css_selector_allowlist: ['.track-click'],
    url_ignorelist: ['/health', '/api/internal'],
  },
});

// before_send replaces older event filtering approaches
posthog.init('phc_...', {
  before_send: (event) => {
    // Return null to drop event, or modified event
    if (event.event === '$pageview' && event.properties?.$current_url?.includes('/admin')) {
      return null; // Don't track admin pages
    }
    return event;
  },
});
```

### Step 3: Upgrade Procedure

```bash
set -euo pipefail
# Create upgrade branch
git checkout -b upgrade/posthog-sdks

# Upgrade posthog-node
npm install posthog-node@latest
# Check for type errors
npx tsc --noEmit 2>&1 | grep -i posthog || echo "No PostHog type errors"

# Upgrade posthog-js
npm install posthog-js@latest
# Check for type errors
npx tsc --noEmit 2>&1 | grep -i posthog || echo "No PostHog type errors"

# Run tests
npm test

# If Python
pip install --upgrade posthog
```

### Step 4: Search for Deprecated Patterns

```bash
set -euo pipefail
# Find files using PostHog
grep -rn "posthog\|PostHog" --include="*.ts" --include="*.tsx" --include="*.js" src/ | \
  grep -v node_modules | grep -v ".d.ts"

# Check for patterns that may need updating
echo "=== Checking for deprecated patterns ==="

# Old import style (posthog-node v3 and earlier)
grep -rn "from 'posthog-node'" --include="*.ts" src/ && echo "Import style: current" || true

# Direct API key in code (should be env var)
grep -rn "phc_\|phx_" --include="*.ts" --include="*.tsx" src/ && \
  echo "WARNING: Hardcoded API key found" || echo "No hardcoded keys"

# Check for sendFeatureFlags usage
grep -rn "sendFeatureFlags" --include="*.ts" src/ || \
  echo "NOTE: No explicit sendFeatureFlags — verify if needed after v5.5.0 upgrade"
```

### Step 5: Validate in Staging

```typescript
// Post-upgrade validation script
import { PostHog } from 'posthog-node';

async function validateUpgrade() {
  const ph = new PostHog(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
    host: 'https://us.i.posthog.com',
    personalApiKey: process.env.POSTHOG_PERSONAL_API_KEY,
  });

  const checks = {
    capture: false,
    flags: false,
    identify: false,
  };

  try {
    // Test capture
    ph.capture({ distinctId: 'upgrade-test', event: 'sdk_upgrade_validated' });
    checks.capture = true;

    // Test feature flags
    const flags = await ph.getAllFlags('upgrade-test');
    checks.flags = typeof flags === 'object';

    // Test identify
    ph.identify({ distinctId: 'upgrade-test', properties: { upgraded: true } });
    checks.identify = true;

    await ph.flush();
  } catch (error) {
    console.error('Validation failed:', error);
  } finally {
    await ph.shutdown();
  }

  console.log('Upgrade validation:', checks);
  const allPassed = Object.values(checks).every(Boolean);
  process.exit(allPassed ? 0 : 1);
}

validateUpgrade();
```

### Step 6: Rollback if Needed

```bash
set -euo pipefail
# Pin to previous version
npm install posthog-node@4.2.1 --save-exact
npm install posthog-js@1.150.0 --save-exact

# Verify rollback
npm test
```

## Version Compatibility

| Package | Node.js Requirement | Key Notes |
|---------|-------------------|-----------|
| posthog-node 5.x | 20+ | `sendFeatureFlags` must be explicit |
| posthog-node 4.x | 18+ | `sendFeatureFlags` was automatic with local eval |
| posthog-js latest | Modern browsers | `before_send` for event filtering, object-based autocapture |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Type errors after upgrade | API changed | Check changelog, update types |
| Flags not sent with events | v5.5.0 change | Add `sendFeatureFlags: true` |
| Autocapture config ignored | Old boolean format | Migrate to object-based autocapture config |
| Test failures | Mock structure changed | Update mocks to match new SDK exports |

## Output

- Upgraded PostHog SDK to latest version
- Deprecated patterns identified and fixed
- All tests passing with new version
- Rollback procedure documented

## Resources

- [posthog-node Changelog](https://github.com/PostHog/posthog-node/releases)
- [posthog-js Changelog](https://github.com/PostHog/posthog-js/releases)
- [PostHog Migration Guides](https://posthog.com/docs/migrate)

## Next Steps

For CI integration during upgrades, see `posthog-ci-integration`.
