# MaintainX Security Basics - Implementation Guide

> Full implementation details and code examples for the `maintainx-security-basics` skill.

# MaintainX Security Basics

## Overview

Secure your MaintainX integration with proper credential management, access controls, and security best practices.

## Prerequisites

- MaintainX account with admin access
- Understanding of environment variables
- Familiarity with secret management concepts

## Security Checklist

- [ ] API keys stored in environment variables or secret manager
- [ ] No credentials in version control
- [ ] HTTPS enforced for all API calls
- [ ] API key rotation schedule established
- [ ] Least privilege principle applied
- [ ] Audit logging enabled
- [ ] Input validation implemented

## Instructions

### Step 1: Secure Credential Storage

```typescript
// NEVER do this:
// const API_KEY = 'mx_live_abc123...';  // Hardcoded - BAD!

// ALWAYS do this:
// src/config/secure-config.ts

import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

interface SecureConfig {
  maintainxApiKey: string;
  maintainxOrgId?: string;
}

// Option 1: Environment variables (development)
function loadFromEnv(): SecureConfig {
  const apiKey = process.env.MAINTAINX_API_KEY;

  if (!apiKey) {
    throw new Error(
      'MAINTAINX_API_KEY not set. ' +
      'Set it as an environment variable or use a secret manager.'
    );
  }

  return {
    maintainxApiKey: apiKey,
    maintainxOrgId: process.env.MAINTAINX_ORG_ID,
  };
}

// Option 2: Google Cloud Secret Manager (production)
async function loadFromSecretManager(): Promise<SecureConfig> {
  const client = new SecretManagerServiceClient();
  const projectId = process.env.GCP_PROJECT_ID;

  const [apiKeyVersion] = await client.accessSecretVersion({
    name: `projects/${projectId}/secrets/maintainx-api-key/versions/latest`,
  });

  const apiKey = apiKeyVersion.payload?.data?.toString();
  if (!apiKey) {
    throw new Error('Failed to load API key from Secret Manager');
  }

  return { maintainxApiKey: apiKey };
}

// Option 3: HashiCorp Vault
async function loadFromVault(): Promise<SecureConfig> {
  const vault = require('node-vault')({
    apiVersion: 'v1',
    endpoint: process.env.VAULT_ADDR,
    token: process.env.VAULT_TOKEN,
  });

  const secret = await vault.read('secret/data/maintainx');
  return {
    maintainxApiKey: secret.data.data.api_key,
  };
}

// Load config based on environment
export async function loadSecureConfig(): Promise<SecureConfig> {
  const env = process.env.NODE_ENV || 'development';

  switch (env) {
    case 'production':
      return loadFromSecretManager();
    case 'staging':
      return loadFromVault();
    default:
      return loadFromEnv();
  }
}
```

### Step 2: Git Security Configuration

```gitignore
# .gitignore - ALWAYS include these

# Environment files
.env
.env.*
!.env.example

# API keys and secrets
*.key
*.pem
secrets/
credentials/

# IDE and local config
.idea/
.vscode/settings.json

# Log files that might contain sensitive data
*.log
logs/
```

```bash
# .env.example - Safe to commit as template
# Copy to .env and fill in values

# MaintainX API Configuration
MAINTAINX_API_KEY=your-api-key-here
MAINTAINX_ORG_ID=optional-org-id

# For secret managers (production)
GCP_PROJECT_ID=your-gcp-project
VAULT_ADDR=https://vault.example.com
```

### Step 3: Pre-commit Hook for Secrets Detection

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Check for potential secrets
PATTERNS=(
  'MAINTAINX_API_KEY\s*=\s*["\x27][a-zA-Z0-9_-]{20,}'
  'mx_live_[a-zA-Z0-9]+'
  'mx_test_[a-zA-Z0-9]+'
  'Bearer\s+[a-zA-Z0-9_-]{20,}'
)

for pattern in "${PATTERNS[@]}"; do
  if git diff --cached | grep -qE "$pattern"; then
    echo "ERROR: Potential secret detected in commit!"
    echo "Pattern: $pattern"
    echo ""
    echo "Remove the secret and use environment variables instead."
    exit 1
  fi
done

echo "Pre-commit security check passed."
```

```bash
# Install the hook
chmod +x .git/hooks/pre-commit
```

### Step 4: Input Validation

```typescript
// src/security/validation.ts
import { z } from 'zod';

// Define schemas for MaintainX data
const WorkOrderInputSchema = z.object({
  title: z.string()
    .min(1, 'Title is required')
    .max(200, 'Title too long')
    .regex(/^[^<>]*$/, 'Invalid characters in title'),  // Prevent XSS
  description: z.string()
    .max(10000, 'Description too long')
    .optional(),
  priority: z.enum(['NONE', 'LOW', 'MEDIUM', 'HIGH']).optional(),
  assetId: z.string()
    .regex(/^[a-zA-Z0-9_-]+$/, 'Invalid asset ID format')
    .optional(),
  locationId: z.string()
    .regex(/^[a-zA-Z0-9_-]+$/, 'Invalid location ID format')
    .optional(),
  dueDate: z.string()
    .datetime()
    .optional(),
});

type WorkOrderInput = z.infer<typeof WorkOrderInputSchema>;

// Validate before API calls
function validateWorkOrderInput(input: unknown): WorkOrderInput {
  return WorkOrderInputSchema.parse(input);
}

// Sanitize output for logging (remove sensitive data)
function sanitizeForLogging(data: any): any {
  const sensitiveFields = ['apiKey', 'token', 'password', 'secret'];
  const sanitized = { ...data };

  for (const field of sensitiveFields) {
    if (sanitized[field]) {
      sanitized[field] = '[REDACTED]';
    }
  }

  return sanitized;
}

// Usage in client
class SecureMaintainXClient {
  async createWorkOrder(input: unknown) {
    // Validate input
    const validatedInput = validateWorkOrderInput(input);

    // Log sanitized data
    console.log('Creating work order:', sanitizeForLogging(validatedInput));

    // Make API call with validated data
    return this.client.createWorkOrder(validatedInput);
  }
}
```

### Step 5: Audit Logging

```typescript
// src/security/audit.ts

interface AuditEntry {
  timestamp: string;
  action: string;
  resource: string;
  resourceId?: string;
  userId?: string;
  ipAddress?: string;
  success: boolean;
  errorMessage?: string;
  requestData?: any;
}

class AuditLogger {
  private logs: AuditEntry[] = [];

  log(entry: Omit<AuditEntry, 'timestamp'>) {
    const fullEntry: AuditEntry = {
      ...entry,
      timestamp: new Date().toISOString(),
      requestData: entry.requestData
        ? sanitizeForLogging(entry.requestData)
        : undefined,
    };

    this.logs.push(fullEntry);

    // In production, send to logging service
    console.log(`[AUDIT] ${fullEntry.action} on ${fullEntry.resource}: ${fullEntry.success ? 'SUCCESS' : 'FAILED'}`);
  }

  // Get audit trail for a resource
  getAuditTrail(resourceId: string): AuditEntry[] {
    return this.logs.filter(l => l.resourceId === resourceId);
  }
}

const auditLogger = new AuditLogger();

// Audit-enabled client wrapper
class AuditedMaintainXClient {
  private client: MaintainXClient;
  private audit: AuditLogger;
  private userId?: string;

  constructor(client: MaintainXClient, userId?: string) {
    this.client = client;
    this.audit = auditLogger;
    this.userId = userId;
  }

  async createWorkOrder(data: any) {
    try {
      const result = await this.client.createWorkOrder(data);

      this.audit.log({
        action: 'CREATE',
        resource: 'WorkOrder',
        resourceId: result.id,
        userId: this.userId,
        success: true,
        requestData: data,
      });

      return result;
    } catch (error: any) {
      this.audit.log({
        action: 'CREATE',
        resource: 'WorkOrder',
        userId: this.userId,
        success: false,
        errorMessage: error.message,
        requestData: data,
      });

      throw error;
    }
  }
}
```

### Step 6: API Key Rotation

```typescript
// scripts/rotate-api-key.ts

async function rotateApiKey() {
  console.log('=== MaintainX API Key Rotation ===\n');

  // Step 1: Generate new key in MaintainX dashboard
  console.log('1. Generate new API key:');
  console.log('   - Go to Settings > Integrations');
  console.log('   - Click "New Key" > "Generate Key"');
  console.log('   - Copy the new key\n');

  // Step 2: Update secret manager
  console.log('2. Update secret manager:');
  console.log('   - GCP: gcloud secrets versions add maintainx-api-key --data-file=newkey.txt');
  console.log('   - Vault: vault kv put secret/maintainx api_key=NEW_KEY\n');

  // Step 3: Deploy with new key
  console.log('3. Deploy application with new key');
  console.log('   - kubectl rollout restart deployment/your-app');
  console.log('   - Or trigger CI/CD pipeline\n');

  // Step 4: Verify new key works
  console.log('4. Verify new key:');
  console.log('   - Run health check script');
  console.log('   - Monitor for authentication errors\n');

  // Step 5: Revoke old key
  console.log('5. Revoke old key (after verification):');
  console.log('   - Go to Settings > Integrations');
  console.log('   - Find old key and click "Revoke"\n');

  // Schedule reminder
  console.log('6. Schedule next rotation (recommended: every 90 days)');
}

rotateApiKey();
```

### Step 7: Network Security

```typescript
// Enforce HTTPS and configure timeouts
import https from 'https';

const secureAxiosConfig = {
  baseURL: 'https://api.getmaintainx.com/v1',  // Always HTTPS
  timeout: 30000,  // 30 second timeout
  httpsAgent: new https.Agent({
    rejectUnauthorized: true,  // Verify SSL certificates
    minVersion: 'TLSv1.2',     // Minimum TLS version
  }),
  headers: {
    'Content-Type': 'application/json',
    'User-Agent': 'YourApp/1.0.0',  // Identify your application
  },
};
```

## Output

- Secure credential storage configured
- Git hooks preventing secret commits
- Input validation implemented
- Audit logging enabled
- Key rotation procedure documented

## Security Checklist Verification

```bash
# Run security checks
npm audit                          # Check for vulnerable dependencies
git secrets --scan                 # Scan for secrets (if git-secrets installed)
npx eslint --rule 'no-hardcoded-credentials: error' src/
```

## Resources

- [MaintainX Security](https://www.getmaintainx.com/security)
- [OWASP API Security](https://owasp.org/API-Security/)
- [Google Cloud Secret Manager](https://cloud.google.com/secret-manager)

## Next Steps

For production deployment, see `maintainx-prod-checklist`.
