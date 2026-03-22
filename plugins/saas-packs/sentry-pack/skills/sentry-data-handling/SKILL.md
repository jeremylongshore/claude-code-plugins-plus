---
name: sentry-data-handling
description: |
  Manage sensitive data, PII scrubbing, and compliance in Sentry.
  Use when configuring PII scrubbing, data retention,
  GDPR compliance, or data security settings.
  Trigger with phrases like "sentry pii", "sentry gdpr",
  "sentry data privacy", "scrub sensitive data sentry".
allowed-tools: Read, Write, Edit, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, sentry, security, compliance, gdpr, pii]

---
# Sentry Data Handling

## Prerequisites
- Sentry project with admin access
- Compliance requirements documented (GDPR, HIPAA, PCI-DSS, SOC 2)
- List of sensitive data patterns to scrub
- Data retention requirements understood

## Instructions

### 1. SDK-Level PII Prevention

The first line of defense is preventing PII from leaving the client:

```typescript
Sentry.init({
  dsn: process.env.SENTRY_DSN,

  // CRITICAL: disable automatic PII collection
  sendDefaultPii: false, // No IP addresses, cookies, user-agent

  beforeSend(event) {
    return scrubEvent(event);
  },

  beforeSendTransaction(event) {
    return scrubEvent(event);
  },

  beforeBreadcrumb(breadcrumb) {
    // Scrub PII from breadcrumbs
    if (breadcrumb.data) {
      const sensitiveKeys = ['password', 'token', 'secret', 'api_key', 'authorization'];
      sensitiveKeys.forEach(key => {
        if (breadcrumb.data[key]) {
          breadcrumb.data[key] = '[REDACTED]';
        }
      });
    }
    return breadcrumb;
  },
});

function scrubEvent(event: Sentry.Event): Sentry.Event | null {
  // Scrub request headers
  if (event.request?.headers) {
    delete event.request.headers['Authorization'];
    delete event.request.headers['Cookie'];
    delete event.request.headers['X-Api-Key'];
    delete event.request.headers['X-Auth-Token'];
  }

  // Scrub request body
  if (event.request?.data) {
    const data = typeof event.request.data === 'string'
      ? tryParseJson(event.request.data)
      : event.request.data;

    if (data && typeof data === 'object') {
      scrubObject(data);
      event.request.data = JSON.stringify(data);
    }
  }

  // Scrub error messages
  if (event.exception?.values) {
    event.exception.values.forEach(exc => {
      if (exc.value) {
        exc.value = scrubPiiFromString(exc.value);
      }
    });
  }

  // Scrub user data (keep id, remove PII)
  if (event.user) {
    const { id, ...pii } = event.user;
    event.user = { id }; // Only keep anonymous ID
  }

  return event;
}

function scrubObject(obj: Record<string, unknown>) {
  const sensitiveKeys = [
    'password', 'passwd', 'secret', 'token', 'api_key', 'apiKey',
    'ssn', 'social_security', 'credit_card', 'cc_number', 'cvv',
    'email', 'phone', 'address', 'dob', 'date_of_birth',
  ];

  for (const key of Object.keys(obj)) {
    if (sensitiveKeys.some(sk => key.toLowerCase().includes(sk))) {
      obj[key] = '[REDACTED]';
    } else if (typeof obj[key] === 'string') {
      obj[key] = scrubPiiFromString(obj[key] as string);
    } else if (typeof obj[key] === 'object' && obj[key] !== null) {
      scrubObject(obj[key] as Record<string, unknown>);
    }
  }
}

function scrubPiiFromString(str: string): string {
  return str
    // Email addresses
    .replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, '[EMAIL]')
    // Credit card numbers (13-19 digits with optional separators)
    .replace(/\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{1,7}\b/g, '[CC_NUMBER]')
    // SSN patterns
    .replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[SSN]')
    // Phone numbers (US format)
    .replace(/\b(\+1)?[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}\b/g, '[PHONE]');
}
```

### 2. Server-Side Data Scrubbing

Configure in **Project Settings > Security & Privacy**:

- **Enable Data Scrubber** — automatically scrubs values matching common PII field names
- **Custom Sensitive Fields** — add: `password`, `secret`, `token`, `api_key`, `ssn`, `credit_card`, `cvv`, `authorization`
- **Safe Fields** — fields to NEVER scrub: `transaction_id`, `order_id`, `request_id`
- **Scrub IP Addresses** — remove IP from all events
- **Scrub Credit Cards** — detect and remove card number patterns

### 3. Advanced Data Scrubbing Rules

Configure in **Project Settings > Security & Privacy > Advanced Data Scrubbing**:

```
# Pattern-based rules
[Remove] [Regex: \d{4}-\d{4}-\d{4}-\d{4}] from [$string]     # Credit cards
[Remove] [Regex: \b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b] from [$string]  # Emails
[Remove] [Regex: \b\d{3}-\d{2}-\d{4}\b] from [$string]        # SSN
[Mask] [Password] from [extra.request_body]                      # Passwords
[Replace] [Credit card] with [REDACTED] from [**]                # All credit cards everywhere
```

### 4. GDPR Compliance

**Right to be Informed:**
- Document that you use Sentry for error tracking in your privacy policy
- Explain what data is collected and why (stack traces, device info, user IDs)

**Right to Erasure (Article 17):**
```bash
# Delete all data for a specific user
# Use the Sentry API to search and delete events by user
curl -X DELETE \
  -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
  "https://sentry.io/api/0/organizations/$SENTRY_ORG/data-deletion/?user_id=USER_ID"

# Or contact Sentry support for full data erasure
```

**Data Minimization:**
```typescript
// Only set user ID, never PII
Sentry.setUser({ id: user.anonymousId });
// NOT: Sentry.setUser({ id: user.id, email: user.email, name: user.name });
```

**Data Processing Agreement:**
- Sign Sentry's DPA at https://sentry.io/legal/dpa/
- Required for GDPR compliance when processing EU user data

### 5. Data Retention Configuration

Configure in **Organization Settings > Data Retention**:
- Default: 90 days for most event data
- Minimum: 30 days
- Maximum: varies by plan (Team: 90 days, Business: 365 days)

### 6. SOC 2 / HIPAA Considerations

```typescript
// For HIPAA environments:
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  sendDefaultPii: false,

  beforeSend(event) {
    // Remove ALL user-identifiable information
    delete event.user;
    delete event.request?.headers;
    delete event.request?.cookies;

    // Remove request body (may contain PHI)
    delete event.request?.data;

    // Keep only technical data
    return event;
  },
});

// For SOC 2:
// - Enable audit logging (Business/Enterprise plan)
// - Configure SSO/SAML
// - Enable IP allowlisting
// - Set up regular access reviews
```

### 7. Verify Data Scrubbing Works

```typescript
// Test script: verify PII is scrubbed
Sentry.withScope((scope) => {
  scope.setUser({
    id: 'test-123',
    email: 'should-be-scrubbed@example.com',
    ip_address: '192.168.1.1',
  });

  scope.setContext('test_data', {
    password: 'should-be-scrubbed',
    credit_card: '4111-1111-1111-1111',
    api_key: 'sk_live_should_be_scrubbed',
    safe_field: 'this should remain',
  });

  Sentry.captureMessage('Data scrubbing verification test');
});

// Then check the event in Sentry dashboard:
// - email should be [REDACTED] or missing
// - password should be [REDACTED]
// - credit_card should be [REDACTED]
// - api_key should be [REDACTED]
// - safe_field should be visible
```

## Output
- Client-side PII scrubbing via beforeSend removing sensitive headers, bodies, and patterns
- Server-side data scrubber enabled with custom sensitive field list
- Advanced scrubbing rules for regex pattern matching
- GDPR compliance with data minimization and erasure capability
- Data retention policies configured per organization requirements
- Verification test confirming scrubbing works end-to-end

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| PII visible in event | `beforeSend` not scrubbing properly | Test with verification script, check regex patterns |
| Over-scrubbing | Safe fields being redacted | Add fields to Safe Fields list in project settings |
| GDPR erasure request | User requests data deletion | Use API or contact Sentry support for full erasure |
| SOC 2 audit finding | Missing audit logs | Upgrade to Business/Enterprise for audit logging |
| `sendDefaultPii: true` in production | Configuration not environment-aware | Gate PII collection behind environment check |

## Resources
- [Data Privacy](https://docs.sentry.io/product/data-management-settings/data-privacy/)
- [Data Scrubbing](https://docs.sentry.io/product/data-management-settings/scrubbing/)
- [GDPR Compliance](https://sentry.io/legal/gdpr/)
- [DPA](https://sentry.io/legal/dpa/)
- [Security](https://sentry.io/security/)
