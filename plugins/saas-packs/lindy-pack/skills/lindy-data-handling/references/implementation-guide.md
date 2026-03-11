# Lindy Data Handling - Implementation Guide

# Lindy Data Handling

## Overview
Best practices for secure and compliant data handling with Lindy AI.

## Prerequisites
- Understanding of data privacy requirements
- Knowledge of applicable regulations (GDPR, CCPA, HIPAA)
- Access to data classification documentation

## Instructions

### Step 1: Data Classification
```typescript
// data/classification.ts
enum DataClassification {
  PUBLIC = 'public',
  INTERNAL = 'internal',
  CONFIDENTIAL = 'confidential',
  RESTRICTED = 'restricted', // PII, PHI, etc.
}

interface DataPolicy {
  classification: DataClassification;
  canSendToLindy: boolean;
  requiresRedaction: boolean;
  retentionDays: number;
}

const policies: Record<DataClassification, DataPolicy> = {
  [DataClassification.PUBLIC]: {
    classification: DataClassification.PUBLIC,
    canSendToLindy: true,
    requiresRedaction: false,
    retentionDays: 365,
  },
  [DataClassification.INTERNAL]: {
    classification: DataClassification.INTERNAL,
    canSendToLindy: true,
    requiresRedaction: false,
    retentionDays: 90,
  },
  [DataClassification.CONFIDENTIAL]: {
    classification: DataClassification.CONFIDENTIAL,
    canSendToLindy: true,
    requiresRedaction: true,
    retentionDays: 30,
  },
  [DataClassification.RESTRICTED]: {
    classification: DataClassification.RESTRICTED,
    canSendToLindy: false,
    requiresRedaction: true,
    retentionDays: 7,
  },
};
```

### Step 2: PII Detection and Redaction
```typescript
// data/pii-redactor.ts
interface PIIPattern {
  name: string;
  pattern: RegExp;
  replacement: string;
}

const piiPatterns: PIIPattern[] = [
  {
    name: 'email',
    pattern: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g,
    replacement: '[EMAIL REDACTED]',
  },
  {
    name: 'phone',
    pattern: /(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}/g,
    replacement: '[PHONE REDACTED]',
  },
  {
    name: 'ssn',
    pattern: /\d{3}-\d{2}-\d{4}/g,
    replacement: '[SSN REDACTED]',
  },
  {
    name: 'credit_card',
    pattern: /\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}/g,
    replacement: '[CREDIT CARD REDACTED]',
  },
  {
    name: 'ip_address',
    pattern: /\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/g,
    replacement: '[IP REDACTED]',
  },
];

export function redactPII(text: string): { redacted: string; found: string[] } {
  let redacted = text;
  const found: string[] = [];

  for (const pattern of piiPatterns) {
    const matches = text.match(pattern.pattern);
    if (matches) {
      found.push(pattern.name);
      redacted = redacted.replace(pattern.pattern, pattern.replacement);
    }
  }

  return { redacted, found };
}
```

### Step 3: Secure Data Pipeline
```typescript
// lib/secure-lindy.ts
import { Lindy } from '@lindy-ai/sdk';
import { redactPII } from '../data/pii-redactor';

export class SecureLindy {
  private lindy: Lindy;

  constructor() {
    this.lindy = new Lindy({ apiKey: process.env.LINDY_API_KEY });
  }

  async runSecure(agentId: string, input: string, options: {
    classification: DataClassification;
    redactPII?: boolean;
  }) {
    // Check if data can be sent to Lindy
    const policy = policies[options.classification];
    if (!policy.canSendToLindy) {
      throw new Error(`Data classification ${options.classification} cannot be sent to Lindy`);
    }

    // Redact PII if required
    let processedInput = input;
    let redactionLog: string[] = [];

    if (policy.requiresRedaction || options.redactPII) {
      const result = redactPII(input);
      processedInput = result.redacted;
      redactionLog = result.found;

      if (redactionLog.length > 0) {
        console.log('PII redacted:', redactionLog);
      }
    }

    // Run agent
    const result = await this.lindy.agents.run(agentId, { input: processedInput });

    // Log for compliance
    await this.logDataAccess({
      agentId,
      classification: options.classification,
      piiRedacted: redactionLog,
      timestamp: new Date(),
    });

    return result;
  }

  private async logDataAccess(log: any): Promise<void> {
    // Store audit log
    console.log('Data access log:', JSON.stringify(log));
  }
}
```

### Step 4: Data Retention Management
```typescript
// data/retention.ts
import { Lindy } from '@lindy-ai/sdk';

interface RetentionPolicy {
  maxAgeDays: number;
  autoDelete: boolean;
}

async function enforceRetention(policy: RetentionPolicy) {
  const lindy = new Lindy({ apiKey: process.env.LINDY_API_KEY });

  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - policy.maxAgeDays);

  // Get old runs
  const runs = await lindy.runs.list({
    before: cutoffDate.toISOString(),
  });

  console.log(`Found ${runs.length} runs older than ${policy.maxAgeDays} days`);

  if (policy.autoDelete) {
    for (const run of runs) {
      await lindy.runs.delete(run.id);
      console.log(`Deleted run: ${run.id}`);
    }
  }
}
```

### Step 5: GDPR Compliance
```typescript
// compliance/gdpr.ts
import { Lindy } from '@lindy-ai/sdk';

class GDPRHandler {
  private lindy: Lindy;

  constructor() {
    this.lindy = new Lindy({ apiKey: process.env.LINDY_API_KEY });
  }

  // Right to Access
  async exportUserData(userId: string): Promise<any> {
    const runs = await this.lindy.runs.list({ userId });
    const agents = await this.lindy.agents.list({ userId });

    return {
      exportDate: new Date().toISOString(),
      userId,
      runs: runs.map(r => ({
        id: r.id,
        agentId: r.agentId,
        createdAt: r.createdAt,
        // Don't include input/output for security
      })),
      agents: agents.map(a => ({
        id: a.id,
        name: a.name,
        createdAt: a.createdAt,
      })),
    };
  }

  // Right to Erasure
  async deleteUserData(userId: string): Promise<void> {
    // Delete all runs
    const runs = await this.lindy.runs.list({ userId });
    for (const run of runs) {
      await this.lindy.runs.delete(run.id);
    }

    // Delete all agents
    const agents = await this.lindy.agents.list({ userId });
    for (const agent of agents) {
      await this.lindy.agents.delete(agent.id);
    }

    console.log(`Deleted all data for user: ${userId}`);
  }
}
```

## Data Handling Checklist
```markdown
[ ] Data classification scheme defined
[ ] PII detection implemented
[ ] Redaction applied before sending to Lindy
[ ] Audit logging enabled
[ ] Retention policies defined
[ ] GDPR/CCPA handlers implemented
[ ] Data access controls configured
[ ] Encryption in transit (HTTPS)
[ ] Regular data audits scheduled
```

## Output
- Data classification system
- PII detection and redaction
- Secure data pipeline
- Retention management
- GDPR compliance handlers

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| PII leaked | Missing redaction | Enable auto-redaction |
| Retention exceeded | No cleanup | Schedule retention job |
| Classification missing | No policy | Default to restricted |

## Resources
- [Lindy Privacy Policy](https://lindy.ai/privacy)
- [Lindy Security](https://lindy.ai/security)
- [GDPR Guidelines](https://gdpr.eu/)

## Next Steps
Proceed to `lindy-enterprise-rbac` for access control.
