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
---

# Sentry Security Basics

## Overview
Configure Sentry to protect sensitive data and follow security best practices.

## Data Scrubbing

### 1. Built-in Scrubbing (Server-Side)
Enable in Sentry Dashboard:
1. Project Settings > Security & Privacy
2. Enable "Data Scrubber"
3. Configure sensitive fields

### 2. Client-Side Scrubbing
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  beforeSend(event) {
    // Scrub user data
    if (event.user) {
      delete event.user.email;
      delete event.user.ip_address;
    }

    // Scrub request body
    if (event.request?.data) {
      const data = JSON.parse(event.request.data);
      delete data.password;
      delete data.creditCard;
      delete data.ssn;
      event.request.data = JSON.stringify(data);
    }

    // Scrub cookies
    if (event.request?.cookies) {
      delete event.request.cookies.session;
      delete event.request.cookies.auth;
    }

    return event;
  },
});
```

### 3. Sensitive Fields Configuration
```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // Don't send specific data
  sendDefaultPii: false, // Disable automatic PII collection

  beforeBreadcrumb(breadcrumb, hint) {
    // Scrub sensitive data from breadcrumbs
    if (breadcrumb.category === 'xhr') {
      const url = breadcrumb.data?.url;
      if (url?.includes('password') || url?.includes('token')) {
        return null;
      }
    }
    return breadcrumb;
  },
});
```

## DSN Security

### Protect Your DSN
```typescript
// DON'T: Expose DSN in public repositories
const dsn = 'https://key@org.ingest.sentry.io/123'; // Bad!

// DO: Use environment variables
const dsn = process.env.SENTRY_DSN;

// DO: Use public DSN for browser (limited scope)
// Browser DSN only allows event ingestion
```

### Key Rotation
```bash
# Generate new DSN in Sentry Dashboard
# Project Settings > Client Keys (DSN) > Generate New Key

# Update environment variables
export SENTRY_DSN="new-dsn-value"

# Disable old key after deployment
```

## Access Control

### Team Permissions
```yaml
# Sentry permission levels
admin: Full control
manager: Project settings, not billing
member: View and resolve issues
billing: Billing only
```

### API Token Scopes
```bash
# Create tokens with minimal scopes
# Settings > Auth Tokens

# Read-only token for monitoring
scopes: project:read, event:read

# CI/CD token for releases
scopes: project:releases, org:read
```

## Secure Configuration

```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // Security settings
  sendDefaultPii: false,
  attachStacktrace: true,

  // Restrict what's captured
  maxBreadcrumbs: 50,
  maxValueLength: 250,

  // Don't capture certain data
  integrations: [
    new Sentry.Integrations.Breadcrumbs({
      console: false, // Don't capture console logs
    }),
  ],

  // Filter sensitive errors
  beforeSend(event, hint) {
    // Don't send authentication failures
    const error = hint.originalException;
    if (error?.message?.includes('authentication')) {
      return null;
    }

    // Redact sensitive data patterns
    if (event.message) {
      event.message = event.message
        .replace(/api[_-]?key[=:]\s*\S+/gi, 'api_key=**REDACTED**')
        .replace(/bearer\s+\S+/gi, 'Bearer **REDACTED**');
    }

    return event;
  },
});
```

## Compliance Considerations

### GDPR
- Enable IP address anonymization
- Configure data retention periods
- Implement right to deletion

### SOC 2
- Use SSO for team access
- Enable audit logs
- Restrict API token permissions

### HIPAA
- Don't send PHI in error messages
- Use custom data scrubbing rules
- Review data handling agreement

## Security Checklist

- [ ] DSN stored in environment variables
- [ ] `sendDefaultPii` set to false
- [ ] Data scrubbing enabled
- [ ] Sensitive field patterns configured
- [ ] API tokens have minimal scopes
- [ ] Team permissions reviewed
- [ ] Old DSN keys disabled

## Resources
- [Sentry Security](https://docs.sentry.io/product/security/)
- [Data Privacy](https://docs.sentry.io/platforms/javascript/data-management/)
