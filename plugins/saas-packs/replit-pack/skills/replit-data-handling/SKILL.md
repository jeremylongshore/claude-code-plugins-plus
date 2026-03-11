---
name: replit-data-handling
description: |
  Implement Replit PII handling, data retention, and GDPR/CCPA compliance patterns.
  Use when handling sensitive data, implementing data redaction, configuring retention policies,
  or ensuring compliance with privacy regulations for Replit integrations.
  Trigger with phrases like "replit data", "replit PII",
  "replit GDPR", "replit data retention", "replit privacy", "replit CCPA".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Replit Data Handling

## Overview
Manage application data securely on Replit. Covers secrets management, database connection security, environment isolation between development and production, and data handling patterns for Replit-hosted applications.

## Prerequisites
- Replit account with workspace access
- Understanding of Replit Secrets
- Database provisioned (PostgreSQL or Replit DB)
- Familiarity with environment variables

## Instructions

### Step 1: Secure Secrets Management
```typescript
// Never hardcode secrets - use Replit Secrets tab
// Validate all required secrets at startup

function validateSecrets(required: string[]): Record<string, string> {
  const secrets: Record<string, string> = {};
  const missing: string[] = [];

  for (const key of required) {
    const value = process.env[key];
    if (!value) {
      missing.push(key);
    } else {
      secrets[key] = value;
    }
  }

  if (missing.length > 0) {
    console.error(`Missing required secrets: ${missing.join(', ')}`);
    console.error('Add them in the Replit Secrets tab (lock icon in sidebar)');
    process.exit(1);
  }

  return secrets;
}

const config = validateSecrets([
  'DATABASE_URL',
  'API_KEY',
  'JWT_SECRET',
  'ENCRYPTION_KEY',
]);
```

### Step 2: Database Connection Security
```typescript
import { Pool } from 'pg';

function createSecurePool(): Pool {
  const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: true } : false,
    max: 10,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 5000,
  });

  // Log connection events without exposing credentials
  pool.on('error', (err) => {
    console.error('Database pool error:', err.message);
    // Never log the full error object (may contain connection string)
  });

  return pool;
}

// Parameterized queries only - never string concatenation
async function findUser(pool: Pool, userId: string) {
  const result = await pool.query(
    'SELECT id, username, created_at FROM users WHERE id = $1',
    [userId]
  );
  return result.rows[0];
}
```

### Step 3: Request Data Sanitization
```typescript
import { z } from 'zod';

// Validate and sanitize all incoming data
const UserInputSchema = z.object({
  name: z.string().min(1).max(100).trim(),
  email: z.string().email().toLowerCase(),
  message: z.string().max(1000).trim(),
});

function sanitizeInput(data: unknown) {
  const result = UserInputSchema.safeParse(data);
  if (!result.success) {
    return { valid: false, errors: result.error.flatten().fieldErrors };
  }
  return { valid: true, data: result.data };
}

// Strip sensitive fields from response
function sanitizeResponse(user: any) {
  const { password_hash, email, phone, ...safe } = user;
  return safe;
}
```

### Step 4: Environment-Based Data Handling
```typescript
const isProduction = process.env.NODE_ENV === 'production';

// Logging: never log sensitive data in production
function safeLog(message: string, data?: any) {
  if (isProduction) {
    // Strip potential PII from logs
    const safeData = data ? JSON.parse(JSON.stringify(data, (key, value) => {
      if (['password', 'token', 'secret', 'email', 'ssn'].includes(key.toLowerCase())) {
        return '[REDACTED]';
      }
      return value;
    })) : undefined;
    console.log(message, safeData);
  } else {
    console.log(message, data);
  }
}

// Error responses: never expose stack traces in production
function errorHandler(err: Error, req: any, res: any, next: any) {
  safeLog('Error:', { message: err.message });

  res.status(500).json({
    error: isProduction ? 'Internal server error' : err.message,
    ...(isProduction ? {} : { stack: err.stack }),
  });
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret undefined | Not set in Secrets tab | Run `validateSecrets` at startup |
| DB connection exposed | Logged in error | Sanitize error messages before logging |
| PII in logs | Full object logged | Use `safeLog` wrapper in production |
| SQL injection | String concatenation | Always use parameterized queries |

## Examples

### Secure API Endpoint
```typescript
app.post('/api/users', async (req, res) => {
  const input = sanitizeInput(req.body);
  if (!input.valid) return res.status(400).json({ errors: input.errors });

  const user = await createUser(pool, input.data);
  res.json(sanitizeResponse(user));
});
```

## Resources
- [Replit Secrets Guide](https://docs.replit.com/programming-ide/workspace-features/secrets)
- [Replit Database](https://docs.replit.com/hosting/databases)
