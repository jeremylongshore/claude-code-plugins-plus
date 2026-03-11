# Apollo Security Basics - Implementation Guide

> Full implementation details and code examples for the `apollo-security-basics` skill.

# Apollo Security Basics

## Overview
Implement security best practices for Apollo.io API integrations including key management, data protection, and access controls.

## API Key Security

### Never Hardcode Keys
```typescript
// BAD - Never do this
const apiKey = 'sk_live_abc123...';

// GOOD - Use environment variables
const apiKey = process.env.APOLLO_API_KEY;

// BETTER - Validate on startup
if (!process.env.APOLLO_API_KEY) {
  throw new Error('APOLLO_API_KEY environment variable is required');
}
```

### Secure Storage
```bash
# .env file (never commit!)
APOLLO_API_KEY=your-api-key-here

# .gitignore (always include!)
.env
.env.local
.env.*.local
*.key
```

### Key Rotation
```typescript
// src/lib/apollo/key-rotation.ts
interface KeyConfig {
  primary: string;
  secondary?: string;
  rotateAt?: Date;
}

class ApiKeyManager {
  private config: KeyConfig;

  constructor() {
    this.config = {
      primary: process.env.APOLLO_API_KEY!,
      secondary: process.env.APOLLO_API_KEY_SECONDARY,
      rotateAt: process.env.APOLLO_KEY_ROTATE_AT
        ? new Date(process.env.APOLLO_KEY_ROTATE_AT)
        : undefined,
    };
  }

  getActiveKey(): string {
    if (this.config.rotateAt && new Date() > this.config.rotateAt) {
      if (this.config.secondary) {
        return this.config.secondary;
      }
      console.warn('Key rotation date passed but no secondary key available');
    }
    return this.config.primary;
  }

  async testKey(key: string): Promise<boolean> {
    try {
      const response = await axios.get('https://api.apollo.io/v1/auth/health', {
        params: { api_key: key },
      });
      return response.status === 200;
    } catch {
      return false;
    }
  }

  async rotateKeys(): Promise<void> {
    if (!this.config.secondary) {
      throw new Error('No secondary key configured for rotation');
    }

    // Verify secondary key works
    const isValid = await this.testKey(this.config.secondary);
    if (!isValid) {
      throw new Error('Secondary key is invalid');
    }

    // Swap keys
    console.log('Rotating API keys...');
    this.config.primary = this.config.secondary;
    this.config.secondary = undefined;
    // TODO: Persist to secure storage
  }
}
```

## Network Security

### HTTPS Only
```typescript
// Force HTTPS
const apolloClient = axios.create({
  baseURL: 'https://api.apollo.io/v1', // Always HTTPS
  timeout: 30000,
});

// Validate SSL certificates (default in production)
// For development ONLY, you might need:
// httpsAgent: new https.Agent({ rejectUnauthorized: false })
```

### IP Allowlisting
```typescript
// If using Apollo Enterprise with IP restrictions
// Configure your server's outbound IP in Apollo settings

// For cloud deployments, use static IPs:
// - Google Cloud: Configure Cloud NAT with static IPs
// - AWS: Use NAT Gateway with Elastic IP
// - Azure: Configure NAT Gateway with public IP
```

## Data Protection

### PII Handling
```typescript
// src/lib/apollo/pii-handler.ts
const PII_FIELDS = ['email', 'phone', 'personal_email', 'mobile_phone'];

function redactPII(data: any, fields: string[] = PII_FIELDS): any {
  if (!data) return data;

  if (Array.isArray(data)) {
    return data.map((item) => redactPII(item, fields));
  }

  if (typeof data === 'object') {
    const result: any = {};
    for (const [key, value] of Object.entries(data)) {
      if (fields.includes(key) && typeof value === 'string') {
        result[key] = redactForLogging(value);
      } else {
        result[key] = redactPII(value, fields);
      }
    }
    return result;
  }

  return data;
}

function redactForLogging(value: string): string {
  if (value.includes('@')) {
    // Email: show first 2 chars and domain
    const [local, domain] = value.split('@');
    return `${local.substring(0, 2)}***@${domain}`;
  }
  // Phone: show last 4 digits
  return `***-***-${value.slice(-4)}`;
}

// Usage in logging
console.log('Contact data:', redactPII(contactData));
```

### Secure Logging
```typescript
// src/lib/apollo/secure-logger.ts
import pino from 'pino';

const logger = pino({
  redact: {
    paths: [
      'api_key',
      'apiKey',
      '*.api_key',
      '*.email',
      '*.phone',
      'headers.authorization',
    ],
    censor: '[REDACTED]',
  },
});

// Apollo request interceptor with secure logging
apolloClient.interceptors.request.use((config) => {
  logger.info({
    type: 'apollo_request',
    method: config.method,
    url: config.url,
    // Don't log full request body
    bodyKeys: config.data ? Object.keys(config.data) : [],
  });
  return config;
});
```

### Data Retention
```typescript
// src/lib/apollo/data-retention.ts
interface CacheConfig {
  ttlMinutes: number;
  maxEntries: number;
}

class SecureCache {
  private cache = new Map<string, { data: any; expiresAt: number }>();
  private config: CacheConfig;

  constructor(config: CacheConfig) {
    this.config = config;
    // Cleanup expired entries every minute
    setInterval(() => this.cleanup(), 60000);
  }

  set(key: string, data: any): void {
    // Enforce max entries
    if (this.cache.size >= this.config.maxEntries) {
      const oldest = [...this.cache.entries()].sort(
        (a, b) => a[1].expiresAt - b[1].expiresAt
      )[0];
      if (oldest) this.cache.delete(oldest[0]);
    }

    this.cache.set(key, {
      data,
      expiresAt: Date.now() + this.config.ttlMinutes * 60 * 1000,
    });
  }

  get(key: string): any | null {
    const entry = this.cache.get(key);
    if (!entry) return null;
    if (Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return null;
    }
    return entry.data;
  }

  private cleanup(): void {
    const now = Date.now();
    for (const [key, entry] of this.cache.entries()) {
      if (now > entry.expiresAt) {
        this.cache.delete(key);
      }
    }
  }

  clear(): void {
    this.cache.clear();
  }
}

// Short TTL for sensitive data
export const apolloCache = new SecureCache({
  ttlMinutes: 15,
  maxEntries: 1000,
});
```

## Access Control

### Role-Based API Key Usage
```typescript
// Different keys for different access levels
const API_KEYS = {
  readonly: process.env.APOLLO_API_KEY_READONLY,
  standard: process.env.APOLLO_API_KEY_STANDARD,
  admin: process.env.APOLLO_API_KEY_ADMIN,
};

function getApiKeyForOperation(operation: string): string {
  const readOnlyOps = ['search', 'enrich', 'get'];
  const adminOps = ['delete', 'bulk_update'];

  if (adminOps.some((op) => operation.includes(op))) {
    return API_KEYS.admin!;
  }
  if (readOnlyOps.some((op) => operation.includes(op))) {
    return API_KEYS.readonly!;
  }
  return API_KEYS.standard!;
}
```

## Security Checklist

### Pre-Deployment
- [ ] API key stored in environment variables
- [ ] .env files added to .gitignore
- [ ] No hardcoded credentials in code
- [ ] HTTPS enforced for all requests
- [ ] Timeout configured for requests
- [ ] Error responses don't leak sensitive data

### Production
- [ ] API key rotation schedule established
- [ ] Logging redacts PII
- [ ] Cache has appropriate TTL
- [ ] Access audit trail enabled
- [ ] Rate limiting implemented
- [ ] IP allowlisting configured (if enterprise)

### Compliance
- [ ] Data retention policy documented
- [ ] GDPR/CCPA requirements met
- [ ] Data processing agreement signed
- [ ] Contact export controls in place
- [ ] Deletion capability implemented

## Output
- Secure API key management
- PII redaction for logging
- Data retention controls
- Role-based access patterns
- Security audit checklist

## Error Handling
| Issue | Mitigation |
|-------|------------|
| Key exposure | Immediate rotation |
| PII in logs | Implement redaction |
| Unauthorized access | Audit and revoke |
| Data breach | Follow incident response |

## Resources
- [Apollo Security Practices](https://www.apollo.io/security)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [GDPR for API Developers](https://gdpr.eu/)

## Next Steps
Proceed to `apollo-prod-checklist` for production deployment.
