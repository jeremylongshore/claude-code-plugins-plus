---
name: sentry-policy-guardrails
description: |
  Implement governance and policy guardrails for Sentry.
  Use when enforcing organizational standards, compliance rules,
  or standardizing Sentry usage across teams.
  Trigger with phrases like "sentry governance", "sentry standards",
  "sentry policy", "enforce sentry configuration".
allowed-tools: Read, Write, Edit, Grep, Bash(node:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, compliance, governance, policy]

---
# Sentry Policy Guardrails

## Prerequisites
- Organization-wide Sentry standards documented
- Team structure and project ownership defined
- Compliance requirements identified (SOC 2, GDPR, HIPAA)
- Shared configuration package repository available

## Instructions

### 1. Shared Configuration Package

Create an internal npm package that enforces organization defaults:

```typescript
// @acme/sentry-config/index.ts
import * as Sentry from '@sentry/node';

// Non-negotiable organization defaults
const ENFORCED_OPTIONS: Partial<Sentry.NodeOptions> = {
  sendDefaultPii: false,        // NEVER send PII by default
  debug: false,                  // NEVER enable debug in production
  maxBreadcrumbs: 50,           // Cap breadcrumb memory usage
  sampleRate: 1.0,              // Capture all errors
  maxValueLength: 500,          // Limit string sizes
};

// Mandatory PII scrubbing
function mandatoryBeforeSend(event: Sentry.Event): Sentry.Event | null {
  // Remove auth headers — non-negotiable
  if (event.request?.headers) {
    delete event.request.headers['Authorization'];
    delete event.request.headers['Cookie'];
    delete event.request.headers['X-Api-Key'];
    delete event.request.headers['X-Auth-Token'];
  }

  // Scrub credit card patterns from everywhere
  const scrub = (str: string) =>
    str.replace(/\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{1,7}\b/g, '[CC_REDACTED]');

  if (event.message) event.message = scrub(event.message);
  if (event.exception?.values) {
    event.exception.values.forEach(v => {
      if (v.value) v.value = scrub(v.value);
    });
  }

  return event;
}

interface InitOptions {
  serviceName: string;
  dsn: string;
  environment?: string;
  version?: string;
  tracesSampleRate?: number;
  beforeSend?: Sentry.NodeOptions['beforeSend'];
}

export function initSentry(options: InitOptions) {
  // Validate required fields
  if (!options.dsn) throw new Error('@acme/sentry-config: DSN is required');
  if (!options.serviceName) throw new Error('@acme/sentry-config: serviceName is required');

  // Validate DSN is from environment variable (heuristic)
  if (options.dsn.startsWith('https://') && !process.env.SENTRY_DSN) {
    console.warn('[Sentry Policy] DSN appears hardcoded — use SENTRY_DSN env var');
  }

  const env = options.environment || process.env.NODE_ENV || 'development';

  Sentry.init({
    dsn: options.dsn,
    environment: env,
    release: `${options.serviceName}@${options.version || 'unknown'}`,
    serverName: options.serviceName,

    // Enforced options (cannot be overridden)
    ...ENFORCED_OPTIONS,

    // Override debug for non-production
    debug: env !== 'production',

    // User-configurable within guardrails
    tracesSampleRate: Math.min(options.tracesSampleRate ?? 0.1, 0.5), // Cap at 50%

    beforeSend(event, hint) {
      // Mandatory scrubbing first
      const scrubbed = mandatoryBeforeSend(event);
      if (!scrubbed) return null;

      // Then user's custom beforeSend
      if (options.beforeSend) {
        return options.beforeSend(scrubbed, hint);
      }
      return scrubbed;
    },

    // Standard tags for all services
    initialScope: {
      tags: {
        service: options.serviceName,
        team: process.env.TEAM_NAME || 'unknown',
        deployment: process.env.DEPLOYMENT_ID || 'unknown',
      },
    },
  });
}
```

### 2. Environment Enforcement

```typescript
// Prevent test data from reaching production
function validateEnvironment(event: Sentry.Event): Sentry.Event | null {
  const env = process.env.NODE_ENV;

  // Block events tagged as test/dev from production project
  if (env === 'production') {
    const tags = event.tags || {};
    if (tags.environment === 'test' || tags.environment === 'development') {
      console.warn('[Sentry Policy] Blocked test event in production');
      return null;
    }
  }

  return event;
}
```

### 3. Project Naming Validation

```bash
#!/bin/bash
# scripts/validate-sentry-projects.sh
# Enforce naming convention: {team}-{service}-{environment}
# Example: payments-api-production

VALID_PATTERN="^[a-z]+-[a-z]+-[a-z]+$"

curl -s -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG/projects/" \
  | python3 -c "
import json, sys, re
projects = json.load(sys.stdin)
pattern = re.compile(r'^[a-z]+-[a-z]+-[a-z]+$')
violations = []
for p in projects:
    slug = p['slug']
    if not pattern.match(slug):
        violations.append(slug)
        print(f'VIOLATION: {slug} — expected format: team-service-environment')

if not violations:
    print('All project names comply with naming policy')
else:
    print(f'\n{len(violations)}/{len(projects)} projects violate naming policy')
    sys.exit(1)
"
```

### 4. Alert Policy Templates

```typescript
// Standard alert templates for new projects

const ALERT_TEMPLATES = {
  // Every project MUST have these alerts
  required: [
    {
      name: 'New Issue in Production',
      conditions: ['event.environment:production', 'event.type:error'],
      actions: ['notify:slack:#alerts-production'],
      frequency: 'once_per_issue',
    },
    {
      name: 'Error Spike',
      type: 'metric',
      trigger: 'count() > 100 in 5m',
      environment: 'production',
      actions: ['notify:pagerduty'],
    },
  ],

  // Recommended for services with SLA
  recommended: [
    {
      name: 'P95 Latency Breach',
      type: 'metric',
      trigger: 'p95(transaction.duration) > 2000 in 10m',
      environment: 'production',
      actions: ['notify:slack:#alerts-performance'],
    },
    {
      name: 'Crash-Free Rate Drop',
      type: 'metric',
      trigger: 'crash_free_rate() < 99% in 1h',
      environment: 'production',
      actions: ['notify:pagerduty'],
    },
  ],
};
```

### 5. Configuration Audit Script

```bash
#!/bin/bash
# scripts/audit-sentry-config.sh — run monthly
set -euo pipefail

echo "=== Sentry Configuration Audit ==="

# Check all projects
PROJECTS=$(curl -s -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG/projects/" \
  | python3 -c "import json,sys; [print(p['slug']) for p in json.load(sys.stdin)]")

for PROJECT in $PROJECTS; do
  echo -e "\n--- $PROJECT ---"

  # Check data scrubbing is enabled
  SETTINGS=$(curl -s -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
    "https://sentry.io/api/0/projects/$SENTRY_ORG/$PROJECT/")

  echo "$SETTINGS" | python3 -c "
import json, sys
p = json.load(sys.stdin)
checks = {
  'Data Scrubber': p.get('dataScrubber', False),
  'Scrub IP Addresses': p.get('scrubIPAddresses', False),
  'Sensitive Fields': len(p.get('sensitiveFields', [])) > 0,
}
for check, passed in checks.items():
    status = 'PASS' if passed else 'FAIL'
    print(f'  [{status}] {check}')
"
done

echo -e "\n=== Audit Complete ==="
```

### 6. CI/CD Enforcement

```yaml
# .github/workflows/sentry-policy.yml
name: Sentry Policy Check

on: [pull_request]

jobs:
  check-sentry-config:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check for hardcoded DSNs
        run: |
          if grep -r "ingest.sentry.io" --include="*.ts" --include="*.js" \
            --exclude-dir=node_modules --exclude-dir=dist src/; then
            echo "FAIL: Hardcoded Sentry DSN found"
            exit 1
          fi

      - name: Check sendDefaultPii is false
        run: |
          if grep -r "sendDefaultPii.*true" --include="*.ts" --include="*.js" \
            --exclude-dir=node_modules src/; then
            echo "FAIL: sendDefaultPii must be false"
            exit 1
          fi

      - name: Check using shared config package
        run: |
          if ! grep -r "@acme/sentry-config" package.json; then
            echo "WARN: Not using shared Sentry config package"
          fi
```

### 7. Token Rotation Policy

```bash
# Quarterly token rotation checklist
# 1. Generate new auth token at sentry.io/settings/auth-tokens/
# 2. Update CI secrets with new token
# 3. Verify CI pipeline works with new token
# 4. Revoke old token
# 5. Update token inventory spreadsheet

# Verify token validity
curl -s -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'Token valid — user: {data.get(\"user\", {}).get(\"email\", \"unknown\")}')
except:
    print('Token INVALID or expired')
    sys.exit(1)
"
```

## Output
- Shared configuration package enforcing organization defaults
- Mandatory PII scrubbing that cannot be overridden
- Project naming validation script for governance
- Alert policy templates for consistent monitoring
- CI/CD checks preventing policy violations
- Token rotation policy with verification

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Teams bypassing shared config | No CI enforcement | Add CI check for `@acme/sentry-config` in package.json |
| PII leaking despite policy | Custom `beforeSend` replacing mandatory scrubbing | Chain mandatory scrubbing before user's `beforeSend` |
| Alert templates not applied | Manual project setup | Automate project creation with terraform or API scripts |
| Token expired in CI | No rotation schedule | Set calendar reminders, automate rotation |

## Resources
- [Organization Settings](https://docs.sentry.io/organization/)
- [Sentry API](https://docs.sentry.io/api/)
- [Project Settings](https://docs.sentry.io/product/settings/)
- [Data Scrubbing](https://docs.sentry.io/product/data-management-settings/scrubbing/)
