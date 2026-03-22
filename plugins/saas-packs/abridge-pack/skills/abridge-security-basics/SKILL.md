---
name: abridge-security-basics
description: |
  Apply HIPAA-compliant security practices for Abridge clinical AI integrations.
  Use when securing PHI in transit/at rest, configuring access controls,
  implementing audit logging, or preparing for HIPAA security audits.
  Trigger: "abridge security", "abridge HIPAA", "abridge PHI protection",
  "abridge access control", "abridge audit logging".
allowed-tools: Read, Write, Edit, Bash(openssl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, healthcare, ai, abridge, security, hipaa]
compatible-with: claude-code
---

# Abridge Security Basics

## Overview

HIPAA-compliant security configuration for Abridge clinical AI integrations. Abridge handles PHI (Protected Health Information) — security is not optional. This skill covers encryption, access control, audit logging, and BAA requirements.

## HIPAA Security Checklist

| Requirement | Implementation | Status |
|-------------|---------------|--------|
| Encryption in transit | TLS 1.3 enforced | Required |
| Encryption at rest | AES-256 for stored PHI | Required |
| Access control | Role-based with MFA | Required |
| Audit logging | All PHI access logged | Required |
| BAA signed | Business Associate Agreement | Required |
| Minimum necessary | Only access needed PHI | Required |
| Breach notification | 60-day notification plan | Required |

## Instructions

### Step 1: Enforce TLS and Certificate Pinning

```typescript
// src/security/tls-config.ts
import https from 'https';
import axios from 'axios';

const abridgeHttpsAgent = new https.Agent({
  minVersion: 'TLSv1.3',           // Enforce TLS 1.3 minimum
  rejectUnauthorized: true,         // Never disable cert validation
  // Optional: certificate pinning for Abridge API
  // ca: fs.readFileSync('./certs/abridge-ca.pem'),
});

const secureClient = axios.create({
  baseURL: process.env.ABRIDGE_BASE_URL,
  httpsAgent: abridgeHttpsAgent,
  headers: {
    'Authorization': `Bearer ${process.env.ABRIDGE_CLIENT_SECRET}`,
    'X-Org-Id': process.env.ABRIDGE_ORG_ID!,
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
  },
});
```

### Step 2: PHI-Safe Audit Logger

```typescript
// src/security/audit-logger.ts
interface AuditEntry {
  timestamp: string;
  action: 'create' | 'read' | 'update' | 'delete' | 'access';
  resource_type: 'session' | 'note' | 'transcript' | 'patient_summary';
  resource_id: string;           // Session/note ID (not PHI)
  actor: string;                 // Provider NPI or system ID
  ip_address: string;
  success: boolean;
  // NEVER include: patient name, DOB, SSN, MRN, diagnosis, note content
}

class HipaaAuditLogger {
  private entries: AuditEntry[] = [];

  log(entry: Omit<AuditEntry, 'timestamp'>): void {
    const fullEntry: AuditEntry = {
      ...entry,
      timestamp: new Date().toISOString(),
    };

    // Validate no PHI leaked into audit log
    const serialized = JSON.stringify(fullEntry);
    if (this.containsPhi(serialized)) {
      console.error('CRITICAL: PHI detected in audit entry — entry blocked');
      return;
    }

    this.entries.push(fullEntry);
    // In production: write to HIPAA-compliant log store (CloudWatch, Splunk, etc.)
    console.log(`AUDIT: ${JSON.stringify(fullEntry)}`);
  }

  private containsPhi(text: string): boolean {
    const phiPatterns = [
      /\b\d{3}-\d{2}-\d{4}\b/,        // SSN
      /\b[A-Z]\d{8}\b/,               // MRN pattern
      /\b\d{1,2}\/\d{1,2}\/\d{4}\b/,  // DOB
    ];
    return phiPatterns.some(p => p.test(text));
  }

  getRetentionPolicy(): { minYears: number; note: string } {
    return {
      minYears: 6,
      note: 'HIPAA requires audit logs retained for minimum 6 years',
    };
  }
}

export { HipaaAuditLogger, AuditEntry };
```

### Step 3: Role-Based Access Control

```typescript
// src/security/rbac.ts
type AbridgeRole = 'clinician' | 'nurse' | 'admin' | 'billing' | 'integration_service';

interface AbridgePermissions {
  canCreateSession: boolean;
  canViewNotes: boolean;
  canViewPatientSummary: boolean;
  canExportData: boolean;
  canManageProviders: boolean;
  canAccessBilling: boolean;
}

const ROLE_PERMISSIONS: Record<AbridgeRole, AbridgePermissions> = {
  clinician: {
    canCreateSession: true, canViewNotes: true, canViewPatientSummary: true,
    canExportData: false, canManageProviders: false, canAccessBilling: false,
  },
  nurse: {
    canCreateSession: true, canViewNotes: true, canViewPatientSummary: true,
    canExportData: false, canManageProviders: false, canAccessBilling: false,
  },
  admin: {
    canCreateSession: false, canViewNotes: false, canViewPatientSummary: false,
    canExportData: true, canManageProviders: true, canAccessBilling: true,
  },
  billing: {
    canCreateSession: false, canViewNotes: false, canViewPatientSummary: false,
    canExportData: false, canManageProviders: false, canAccessBilling: true,
  },
  integration_service: {
    canCreateSession: true, canViewNotes: true, canViewPatientSummary: false,
    canExportData: false, canManageProviders: false, canAccessBilling: false,
  },
};

function checkPermission(role: AbridgeRole, action: keyof AbridgePermissions): boolean {
  return ROLE_PERMISSIONS[role]?.[action] ?? false;
}
```

### Step 4: Secrets Management

```typescript
// src/security/secrets.ts
// Never hardcode credentials — use environment or secret manager

async function loadAbridgeSecrets(): Promise<Record<string, string>> {
  // Option 1: Environment variables (minimum viable)
  // Option 2: AWS Secrets Manager / GCP Secret Manager (recommended)
  // Option 3: HashiCorp Vault (enterprise)

  // Example: GCP Secret Manager
  const { SecretManagerServiceClient } = await import('@google-cloud/secret-manager');
  const client = new SecretManagerServiceClient();

  const secrets: Record<string, string> = {};
  const secretNames = ['abridge-client-secret', 'abridge-org-id', 'epic-client-secret'];

  for (const name of secretNames) {
    const [version] = await client.accessSecretVersion({
      name: `projects/${process.env.GCP_PROJECT}/secrets/${name}/versions/latest`,
    });
    secrets[name] = version.payload?.data?.toString() || '';
  }

  return secrets;
}
```

## Output

- TLS 1.3 enforcement with optional cert pinning
- HIPAA-compliant audit logger with PHI leak detection
- Role-based access control matrix
- Secrets loaded from cloud secret manager

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| TLS handshake failure | Server doesn't support TLS 1.3 | Verify Abridge endpoint; check proxy |
| PHI in logs | Audit logger bypass | Add PHI detection to all log paths |
| Permission denied | Wrong role | Check RBAC matrix for required role |

## Resources

- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/)
- [Abridge Security](https://www.abridge.com/security)
- [SMART on FHIR Security](https://hl7.org/fhir/smart-app-launch/scopes-and-launch-context.html)

## Next Steps

For production deployment checklist, see `abridge-prod-checklist`.
