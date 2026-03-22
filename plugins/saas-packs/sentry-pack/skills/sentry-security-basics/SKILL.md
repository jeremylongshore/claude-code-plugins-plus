---
name: sentry-security-basics
description: |
  Configure Sentry security settings and data protection.
  Use when setting up data scrubbing, managing sensitive data,
  or configuring security policies.
  Trigger with phrases like "sentry security", "sentry PII",
  "sentry data scrubbing", "secure sentry".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, security, pii, data-scrubbing]

---
# Sentry Security Basics

## Prerequisites
- Sentry project with admin access
- Compliance requirements identified (GDPR, SOC 2, HIPAA)
- Sensitive data patterns documented (PII, API keys, tokens)
- Access control requirements defined

## Instructions

### 1. DSN Security

The DSN is a public key — it identifies your project but cannot read data. Still, treat it carefully:

```typescript
// Store in environment variables, never hardcode
Sentry.init({
  dsn: process.env.SENTRY_DSN,
});

// .gitignore
.env
.env.local
.env.production
```

```bash
# Verify no hardcoded DSNs in codebase
grep -r "ingest.sentry.io" --include="*.ts" --include="*.js" \
  --exclude-dir=node_modules --exclude-dir=dist src/
```

### 2. Disable Default PII Collection

```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // CRITICAL: disable automatic PII collection
  sendDefaultPii: false, // Default is false, but be explicit

  // Disable debug in production
  debug: process.env.NODE_ENV !== 'production',
});
```

When `sendDefaultPii: false`:
- No IP addresses collected
- No cookie values sent
- No user-agent strings in request data
- No request body data

### 3. Client-Side Data Scrubbing with beforeSend

```typescript
Sentry.init({
  beforeSend(event) {
    // Scrub authorization headers
    if (event.request?.headers) {
      delete event.request.headers['Authorization'];
      delete event.request.headers['Cookie'];
      delete event.request.headers['X-Api-Key'];
    }

    // Scrub request body data
    if (event.request?.data) {
      const data = typeof event.request.data === 'string'
        ? JSON.parse(event.request.data)
        : event.request.data;

      const sensitiveFields = ['password', 'ssn', 'credit_card', 'token', 'secret'];
      sensitiveFields.forEach(field => {
        if (data[field]) data[field] = '[REDACTED]';
      });

      event.request.data = JSON.stringify(data);
    }

    // Scrub PII from error messages
    if (event.exception?.values) {
      event.exception.values.forEach(exc => {
        if (exc.value) {
          // Redact email addresses
          exc.value = exc.value.replace(
            /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g,
            '[EMAIL_REDACTED]'
          );
          // Redact credit card numbers
          exc.value = exc.value.replace(
            /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g,
            '[CC_REDACTED]'
          );
        }
      });
    }

    return event;
  },
});
```

### 4. Server-Side Data Scrubbing

Configure in **Project Settings > Security & Privacy**:

- **Data Scrubber** — automatically scrubs fields matching common PII patterns
- **Sensitive Fields** — add custom field names: `password`, `ssn`, `credit_card_number`, `api_key`, `secret`, `token`
- **Safe Fields** — exclude fields from scrubbing (e.g., `transaction_id`)
- **IP Address Scrubbing** — remove or hash IP addresses
- **Scrub Credit Cards** — detect and remove card numbers

### 5. Auth Token Security

```bash
# Generate tokens with MINIMAL required scopes
# For CI releases: project:releases (read + write)
# For issue management: project:read, event:read
# NEVER use org:admin scope in CI

# Store in CI secrets, not in code
# GitHub Actions: Settings > Secrets > SENTRY_AUTH_TOKEN
# GitLab CI: Settings > CI/CD > Variables (protected + masked)
```

Token hygiene:
- Create separate tokens per CI pipeline
- Set token expiration dates
- Rotate tokens quarterly
- Revoke unused tokens immediately
- Never use the same token for dev and production

### 6. Team Access Control

```bash
# Create team with API
curl -X POST \
  -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"slug": "backend-team"}' \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG/teams/"

# Assign project to team (limits who can see project errors)
curl -X POST \
  -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/projects/$SENTRY_ORG/$SENTRY_PROJECT/teams/backend-team/"
```

### 7. Allowed Domains (Browser SDK)

Restrict which domains can send events to your DSN:

Configure in **Project Settings > Client Keys > Allowed Domains**:
```
example.com
*.example.com
staging.example.com
```

This prevents other sites from sending spam events to your project using your public DSN.

### 8. Audit Logging

Enable audit logging in **Organization Settings > Audit Log** (Business/Enterprise plan):
- Tracks member additions/removals
- Records permission changes
- Logs project creation/deletion
- Monitors integration changes

## Output
- `sendDefaultPii: false` configured explicitly
- Client-side scrubbing removing sensitive headers, bodies, and PII patterns
- Server-side data scrubber enabled with custom sensitive fields
- Auth tokens created with minimal scopes and expiration dates
- Allowed domains restricting event sources (browser projects)
- Audit logging enabled for compliance tracking

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| PII in error events | `sendDefaultPii: true` or PII in error messages | Set `sendDefaultPii: false`, add `beforeSend` scrubbing |
| Token compromised | Token in source code or leaked | Revoke immediately at sentry.io/settings/auth-tokens/, rotate |
| Unauthorized events | DSN used from unauthorized domain | Configure allowed domains in Client Keys settings |
| Audit log gaps | Organization plan doesn't include audit logs | Upgrade to Business or Enterprise plan |

## Resources
- [Data Privacy](https://docs.sentry.io/product/data-management-settings/data-privacy/)
- [Data Scrubbing](https://docs.sentry.io/product/data-management-settings/scrubbing/)
- [Security Policy](https://sentry.io/security/)
- [Auth Tokens](https://docs.sentry.io/api/guides/create-auth-token/)
