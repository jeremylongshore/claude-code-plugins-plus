---
name: hubspot-policy-guardrails
description: |
  Implement HubSpot lint rules, secret scanning, and CI policy checks.
  Use when setting up code quality rules for HubSpot integrations,
  preventing token leaks, or configuring CI guardrails.
  Trigger with phrases like "hubspot policy", "hubspot lint",
  "hubspot guardrails", "hubspot security check", "hubspot eslint rules".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Policy & Guardrails

## Overview

Automated policy enforcement for HubSpot integrations: secret scanning, ESLint rules, CI checks for token leaks, and runtime guardrails.

## Prerequisites

- ESLint configured in project
- CI/CD pipeline (GitHub Actions)
- TypeScript for compile-time enforcement

## Instructions

### Step 1: Secret Scanning (Prevent Token Leaks)

```yaml
# .github/workflows/hubspot-security.yml
name: HubSpot Security Scan
on: [push, pull_request]

jobs:
  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Scan for HubSpot private app tokens
        run: |
          # Pattern: pat-{region}{number}-{uuid}
          if grep -rE "pat-[a-z]{2}[0-9]-[a-f0-9-]{36}" \
            --include="*.ts" --include="*.js" --include="*.json" --include="*.yaml" \
            --exclude-dir=node_modules --exclude-dir=.git .; then
            echo "::error::HubSpot private app token found in source code!"
            echo "Rotate this token immediately in HubSpot Settings > Private Apps"
            exit 1
          fi

      - name: Scan for deprecated API keys
        run: |
          # Pattern: hapikey=uuid
          if grep -rE "hapikey=[a-f0-9-]{36}" \
            --include="*.ts" --include="*.js" --include="*.env.example" \
            --exclude-dir=node_modules .; then
            echo "::error::Deprecated HubSpot API key found! Migrate to private app tokens."
            exit 1
          fi

      - name: Verify .gitignore includes .env files
        run: |
          if ! grep -q "^\.env$" .gitignore; then
            echo "::error::.gitignore missing .env entry"
            exit 1
          fi
```

### Step 2: ESLint Rule -- No Deprecated API Key Auth

```javascript
// eslint-rules/no-hubspot-api-key.js
module.exports = {
  meta: {
    type: 'problem',
    docs: { description: 'Disallow deprecated HubSpot API key authentication' },
    messages: {
      noApiKey: 'HubSpot API keys are deprecated. Use accessToken from a private app instead.',
      useAccessToken: 'Use { accessToken: process.env.HUBSPOT_ACCESS_TOKEN } instead of { apiKey }',
    },
  },
  create(context) {
    return {
      Property(node) {
        if (
          node.key.type === 'Identifier' &&
          node.key.name === 'apiKey' &&
          node.parent?.parent?.callee?.name === 'Client'
        ) {
          context.report({ node, messageId: 'noApiKey' });
        }
      },
      Literal(node) {
        if (typeof node.value === 'string') {
          // Detect hardcoded private app tokens
          if (node.value.match(/^pat-[a-z]{2}\d-[a-f0-9-]{36}$/)) {
            context.report({
              node,
              message: 'Hardcoded HubSpot access token detected. Use environment variable.',
            });
          }
          // Detect deprecated API keys
          if (node.value.match(/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/) &&
              node.parent?.key?.name === 'apiKey') {
            context.report({ node, messageId: 'useAccessToken' });
          }
        }
      },
    };
  },
};
```

### Step 3: TypeScript Compile-Time Guardrails

```typescript
// src/hubspot/strict-types.ts

// Enforce that all HubSpot operations go through the service layer
// (not raw client calls scattered throughout the codebase)

// BAD: Using raw client anywhere
// const client = new hubspot.Client({ accessToken: '...' });
// client.crm.contacts.basicApi.create(...); // unguarded

// GOOD: All operations through typed service
interface IContactService {
  findByEmail(email: string): Promise<Contact | null>;
  create(data: CreateContactInput): Promise<Contact>;
  update(id: string, data: UpdateContactInput): Promise<Contact>;
  archive(id: string): Promise<void>;
}

// Enforce required properties at compile time
interface CreateContactInput {
  email: string;           // required
  firstname?: string;
  lastname?: string;
  lifecyclestage?: 'subscriber' | 'lead' | 'marketingqualifiedlead' |
    'salesqualifiedlead' | 'opportunity' | 'customer' | 'evangelist';
}

// Prevent passing unknown/dangerous properties
type UpdateContactInput = Partial<Omit<CreateContactInput, 'email'>>;

// Compile-time check: lifecycle stage must be valid
const validStage: CreateContactInput = {
  email: 'test@example.com',
  lifecyclestage: 'customer', // TypeScript enforces valid values
};

// This would fail at compile time:
// lifecyclestage: 'invalid_stage' // Type error
```

### Step 4: Runtime Guardrails

```typescript
// Prevent dangerous operations in production
const BLOCKED_IN_PROD: Record<string, string> = {
  'batch/archive': 'Bulk archiving is blocked in production',
  'gdpr-delete': 'GDPR delete requires manual approval in production',
};

function guardOperation(path: string): void {
  if (process.env.NODE_ENV !== 'production') return;

  for (const [pattern, message] of Object.entries(BLOCKED_IN_PROD)) {
    if (path.includes(pattern)) {
      throw new Error(`BLOCKED: ${message}. Environment: production.`);
    }
  }
}

// Rate limit self-protection (don't consume entire portal quota)
class SelfRateLimiter {
  private callsThisSecond = 0;
  private callsToday = 0;
  private lastSecond = Math.floor(Date.now() / 1000);
  private lastDay = new Date().toDateString();

  private maxPerSecond: number;
  private maxPerDay: number;

  constructor(maxPerSecond = 8, maxPerDay = 400000) {
    this.maxPerSecond = maxPerSecond; // leave 2/sec headroom for other apps
    this.maxPerDay = maxPerDay;       // leave 100K/day headroom
  }

  check(): void {
    const now = Math.floor(Date.now() / 1000);
    const today = new Date().toDateString();

    if (now !== this.lastSecond) {
      this.callsThisSecond = 0;
      this.lastSecond = now;
    }
    if (today !== this.lastDay) {
      this.callsToday = 0;
      this.lastDay = today;
    }

    this.callsThisSecond++;
    this.callsToday++;

    if (this.callsThisSecond > this.maxPerSecond) {
      throw new Error(
        `Self rate limit: ${this.callsThisSecond}/${this.maxPerSecond} per second`
      );
    }
    if (this.callsToday > this.maxPerDay) {
      throw new Error(
        `Self rate limit: ${this.callsToday}/${this.maxPerDay} per day`
      );
    }
  }
}
```

### Step 5: Pre-Commit Hook

```bash
#!/bin/bash
# .husky/pre-commit

# Scan for HubSpot tokens in staged files
PATTERN="pat-[a-z]{2}[0-9]-[a-f0-9-]{36}"
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E "\.(ts|js|json|yaml|yml)$")

if [ -n "$STAGED_FILES" ]; then
  if echo "$STAGED_FILES" | xargs grep -lE "$PATTERN" 2>/dev/null; then
    echo "ERROR: HubSpot access token found in staged files!"
    echo "Remove the token and use environment variables instead."
    exit 1
  fi
fi
```

## Output

- CI secret scanning for HubSpot tokens (private app and legacy API keys)
- ESLint rules preventing deprecated auth and hardcoded tokens
- TypeScript types enforcing valid property values at compile time
- Runtime guardrails blocking dangerous production operations
- Self-rate limiting to avoid consuming entire portal quota
- Pre-commit hook catching tokens before they hit git

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| False positive on UUID | Pattern too broad | Check context (parent node name) |
| Token leaked to git | Pre-commit hook skipped | Enforce in CI as backup |
| Self-limiter too strict | Conservative defaults | Adjust based on portal usage |
| ESLint rule not running | Plugin not registered | Add to `.eslintrc` plugins array |

## Resources

- [HubSpot Security Best Practices](https://developers.hubspot.com/docs/guides/apps/private-apps/overview)
- [ESLint Custom Rules](https://eslint.org/docs/latest/extend/custom-rules)
- [Husky Pre-commit Hooks](https://typicode.github.io/husky/)

## Next Steps

For architecture blueprints, see `hubspot-architecture-variants`.
