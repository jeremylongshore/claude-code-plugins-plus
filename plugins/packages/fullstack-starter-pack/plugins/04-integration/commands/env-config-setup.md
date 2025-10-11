---
description: Generate environment configuration files and validation schemas
shortcut: ecs
category: devops
difficulty: beginner
estimated_time: 2-3 minutes
---

# Environment Config Setup

Generates environment configuration files (.env templates, validation schemas, and type-safe config loading) for multiple environments.

## What This Command Does

**Generated Configuration:**
-  .env.example (committed template)
-  .env.development, .env.production
-  Config validation schema (Zod)
-  Type-safe config loader
-  Secret management guidance
-  Docker environment setup

**Output:** Complete environment configuration system

**Time:** 2-3 minutes

---

## Usage

```bash
# Generate basic environment config
/env-config-setup

# Shortcut
/ecs --services database,redis,email

# With specific platform
/ecs --platform aws --features secrets-manager
```

---

## Generated Files

### **.env.example** (Template - Committed to Repo)

```bash
# Application
NODE_ENV=development
PORT=3000
APP_NAME=My Application
APP_URL=http://localhost:3000

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/myapp
DATABASE_POOL_MIN=2
DATABASE_POOL_MAX=10

# Redis
REDIS_URL=redis://localhost:6379
REDIS_PREFIX=myapp:

# Authentication
JWT_SECRET=generate-random-32-char-secret-here
JWT_EXPIRES_IN=15m
JWT_REFRESH_SECRET=generate-random-32-char-refresh-secret
JWT_REFRESH_EXPIRES_IN=7d

# Email (SendGrid)
SENDGRID_API_KEY=SG.your-api-key-here
FROM_EMAIL=[email protected]

# AWS (Optional)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
S3_BUCKET=your-bucket-name

# External APIs
STRIPE_SECRET_KEY=sk_test_your-stripe-key
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
LOG_LEVEL=info

# Feature Flags
ENABLE_FEATURE_X=false
```

### **.env.development**

```bash
NODE_ENV=development
PORT=3000
DATABASE_URL=postgresql://postgres:password@localhost:5432/myapp_dev
REDIS_URL=redis://localhost:6379
LOG_LEVEL=debug
```

### **.env.production**

```bash
NODE_ENV=production
PORT=8080
# Use environment variables or secrets manager for sensitive values
DATABASE_URL=${DATABASE_URL}
REDIS_URL=${REDIS_URL}
JWT_SECRET=${JWT_SECRET}
LOG_LEVEL=warn
```

### **config/env.ts** (Type-Safe Config Loader)

```typescript
import { z } from 'zod'
import dotenv from 'dotenv'

// Load appropriate .env file
const envFile = process.env.NODE_ENV === 'production'
  ? '.env.production'
  : '.env.development'

dotenv.config({ path: envFile })

// Define validation schema
const envSchema = z.object({
  // Application
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.coerce.number().min(1).max(65535).default(3000),
  APP_NAME: z.string().min(1),
  APP_URL: z.string().url(),

  // Database
  DATABASE_URL: z.string().url(),
  DATABASE_POOL_MIN: z.coerce.number().min(0).default(2),
  DATABASE_POOL_MAX: z.coerce.number().min(1).default(10),

  // Redis
  REDIS_URL: z.string().url(),
  REDIS_PREFIX: z.string().default(''),

  // Authentication
  JWT_SECRET: z.string().min(32),
  JWT_EXPIRES_IN: z.string().default('15m'),
  JWT_REFRESH_SECRET: z.string().min(32),
  JWT_REFRESH_EXPIRES_IN: z.string().default('7d'),

  // Email
  SENDGRID_API_KEY: z.string().startsWith('SG.'),
  FROM_EMAIL: z.string().email(),

  // AWS (optional)
  AWS_ACCESS_KEY_ID: z.string().optional(),
  AWS_SECRET_ACCESS_KEY: z.string().optional(),
  AWS_REGION: z.string().default('us-east-1'),
  S3_BUCKET: z.string().optional(),

  // External APIs
  STRIPE_SECRET_KEY: z.string().startsWith('sk_'),
  STRIPE_WEBHOOK_SECRET: z.string().startsWith('whsec_'),

  // Monitoring
  SENTRY_DSN: z.string().url().optional(),
  LOG_LEVEL: z.enum(['error', 'warn', 'info', 'debug']).default('info'),

  // Feature Flags
  ENABLE_FEATURE_X: z.coerce.boolean().default(false)
})

// Parse and validate
const parsedEnv = envSchema.safeParse(process.env)

if (!parsedEnv.success) {
  console.error(' Invalid environment variables:')
  console.error(parsedEnv.error.flatten().fieldErrors)
  process.exit(1)
}

export const env = parsedEnv.data

// Type-safe access
export type Env = z.infer<typeof envSchema>
```

### **config/secrets.ts** (AWS Secrets Manager)

```typescript
import { SecretsManager } from '@aws-sdk/client-secrets-manager'

const client = new SecretsManager({ region: process.env.AWS_REGION })

export async function loadSecrets(secretName: string) {
  try {
    const response = await client.getSecretValue({ SecretId: secretName })
    return JSON.parse(response.SecretString || '{}')
  } catch (error) {
    console.error('Failed to load secrets:', error)
    throw error
  }
}

// Usage
const secrets = await loadSecrets('prod/myapp/secrets')
process.env.JWT_SECRET = secrets.JWT_SECRET
```

### **docker-compose.env.yml**

```yaml
version: '3.8'

services:
  app:
    build: .
    env_file:
      - .env.development
    environment:
      - NODE_ENV=development
      - PORT=3000
    ports:
      - "3000:3000"

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
      POSTGRES_DB: ${POSTGRES_DB:-myapp_dev}
    ports:
      - "5432:5432"
```

---

## Security Best Practices

**1. Never Commit Secrets:**
```bash
# .gitignore
.env
.env.local
.env.*.local
.env.production
*.key
*.pem
secrets/
```

**2. Use Secret Rotation:**
```bash
# Rotate secrets regularly
# Use AWS Secrets Manager, GCP Secret Manager, or Azure Key Vault
# Example: Rotate JWT secrets every 30 days
```

**3. Least Privilege:**
```bash
# Only provide necessary permissions
# Use separate credentials for dev/staging/prod
# Implement role-based access control
```

**4. Environment Validation:**
```typescript
// Validate on startup
if (process.env.NODE_ENV === 'production') {
  if (!env.JWT_SECRET || env.JWT_SECRET.length < 32) {
    throw new Error('Production JWT_SECRET must be at least 32 characters')
  }
}
```

---

## Secret Generation

```bash
# Generate secure random secrets
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"

# Or use openssl
openssl rand -hex 32

# For JWT secrets (base64)
openssl rand -base64 32
```

---

## Platform-Specific Setup

**Vercel:**
```bash
# Set environment variables via CLI
vercel env add DATABASE_URL production
vercel env add JWT_SECRET production
```

**Railway:**
```bash
# Environment variables in dashboard
# Or via railway.json
{
  "deploy": {
    "envVars": {
      "NODE_ENV": "production"
    }
  }
}
```

**AWS ECS:**
```json
{
  "containerDefinitions": [{
    "secrets": [
      {
        "name": "DATABASE_URL",
        "valueFrom": "arn:aws:secretsmanager:region:account:secret:name"
      }
    ]
  }]
}
```

---

## Related Commands

- `/auth-setup` - Generate authentication system
- `/project-scaffold` - Generate full project structure

---

**Manage secrets safely. Configure environments easily. Deploy confidently.** ️
