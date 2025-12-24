# Compliance & Audit Guide: Security and Regulatory Compliance

**Production Playbook for Security Teams and Compliance Officers**

Ensuring Claude Code plugin workflows meet SOC 2, GDPR, HIPAA, and other regulatory requirements is critical for enterprise deployments. This playbook provides audit logging implementation, compliance checklists, data privacy patterns, access controls, and security hardening procedures for AI-powered automation.

## Table of Contents

1. [Regulatory Frameworks](#regulatory-frameworks)
2. [Audit Logging](#audit-logging)
3. [Data Privacy & Retention](#data-privacy--retention)
4. [Access Controls](#access-controls)
5. [SOC 2 Compliance](#soc-2-compliance)
6. [GDPR Compliance](#gdpr-compliance)
7. [HIPAA Compliance](#hipaa-compliance)
8. [Security Hardening](#security-hardening)
9. [Best Practices](#best-practices)
10. [Tools & Resources](#tools--resources)
11. [Summary](#summary)

---

## Regulatory Frameworks

### Compliance Requirements Overview

| Framework | Scope | Key Requirements | Claude Code Impact |
|-----------|-------|------------------|-------------------|
| **SOC 2 Type II** | Service organizations | Security, availability, confidentiality | Audit logs, access controls, encryption |
| **GDPR** | EU data subjects | Consent, data minimization, right to erasure | Data retention, anonymization, deletion |
| **HIPAA** | Healthcare data (PHI) | Encryption, access logs, BAA required | Self-hosted, audit trails, no cloud APIs |
| **PCI DSS** | Payment card data | Encryption, access controls, logging | Tokenization, secure storage |
| **ISO 27001** | Information security | Risk management, controls framework | Security policies, incident response |

### Risk Assessment

```typescript
interface ComplianceRisk {
  framework: 'SOC2' | 'GDPR' | 'HIPAA' | 'PCI' | 'ISO27001';
  requirement: string;
  currentState: 'compliant' | 'non-compliant' | 'partial';
  risk: 'critical' | 'high' | 'medium' | 'low';
  remediation: string;
  dueDate: Date;
}

const risks: ComplianceRisk[] = [
  {
    framework: 'GDPR',
    requirement: 'Right to erasure (Article 17)',
    currentState: 'non-compliant',
    risk: 'high',
    remediation: 'Implement conversation deletion API',
    dueDate: new Date('2025-12-31')
  },
  {
    framework: 'SOC2',
    requirement: 'Audit logging (CC6.1)',
    currentState: 'partial',
    risk: 'medium',
    remediation: 'Enable immutable audit logs with timestamps',
    dueDate: new Date('2025-12-28')
  }
];
```

---

## Audit Logging

### Comprehensive Audit Trail

**Required Events to Log**:
```typescript
enum AuditEventType {
  // Authentication
  USER_LOGIN = 'user.login',
  USER_LOGOUT = 'user.logout',
  API_KEY_CREATED = 'api_key.created',
  API_KEY_REVOKED = 'api_key.revoked',

  // Data Access
  CONVERSATION_READ = 'conversation.read',
  CONVERSATION_CREATED = 'conversation.created',
  CONVERSATION_DELETED = 'conversation.deleted',
  DATA_EXPORT = 'data.export',

  // Configuration Changes
  PLUGIN_INSTALLED = 'plugin.installed',
  PLUGIN_UNINSTALLED = 'plugin.uninstalled',
  SETTINGS_CHANGED = 'settings.changed',

  // Security Events
  AUTHENTICATION_FAILED = 'auth.failed',
  AUTHORIZATION_DENIED = 'authz.denied',
  ENCRYPTION_KEY_ROTATED = 'encryption.key_rotated',
  SUSPICIOUS_ACTIVITY = 'security.suspicious'
}

interface AuditLog {
  id: string;
  timestamp: number;
  eventType: AuditEventType;
  userId: string;
  ipAddress: string;
  userAgent: string;
  resource: {
    type: string;
    id: string;
  };
  action: string;
  outcome: 'success' | 'failure';
  metadata: Record<string, any>;
  signature: string;  // HMAC for tamper detection
}
```

### Implementation

```typescript
import crypto from 'crypto';

class AuditLogger {
  private readonly secretKey: string;

  constructor(secretKey: string) {
    this.secretKey = secretKey;
  }

  async log(event: Omit<AuditLog, 'id' | 'timestamp' | 'signature'>): Promise<void> {
    const auditLog: AuditLog = {
      id: crypto.randomUUID(),
      timestamp: Date.now(),
      ...event,
      signature: '' // Computed below
    };

    // Generate HMAC signature for tamper detection
    const data = JSON.stringify({
      id: auditLog.id,
      timestamp: auditLog.timestamp,
      eventType: auditLog.eventType,
      userId: auditLog.userId,
      resource: auditLog.resource,
      action: auditLog.action,
      outcome: auditLog.outcome
    });

    auditLog.signature = crypto
      .createHmac('sha256', this.secretKey)
      .update(data)
      .digest('hex');

    // Write to immutable log storage
    await this.writeToStorage(auditLog);
  }

  private async writeToStorage(log: AuditLog): Promise<void> {
    // Option 1: Append-only file (WORM - Write Once Read Many)
    await appendFile('/var/log/audit/audit.jsonl', JSON.stringify(log) + '\n');

    // Option 2: PostgreSQL with audit triggers
    await db.query(
      'INSERT INTO audit_logs (id, timestamp, event_type, user_id, data, signature) VALUES ($1, $2, $3, $4, $5, $6)',
      [log.id, log.timestamp, log.eventType, log.userId, log, log.signature]
    );

    // Option 3: Send to SIEM (Splunk, ELK)
    await fetch('https://siem.example.com/audit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(log)
    });
  }

  async verify(log: AuditLog): Promise<boolean> {
    const data = JSON.stringify({
      id: log.id,
      timestamp: log.timestamp,
      eventType: log.eventType,
      userId: log.userId,
      resource: log.resource,
      action: log.action,
      outcome: log.outcome
    });

    const expectedSignature = crypto
      .createHmac('sha256', this.secretKey)
      .update(data)
      .digest('hex');

    return log.signature === expectedSignature;
  }
}
```

### Usage Example

```typescript
const auditor = new AuditLogger(process.env.AUDIT_SECRET_KEY);

// Log authentication event
await auditor.log({
  eventType: AuditEventType.USER_LOGIN,
  userId: 'user-123',
  ipAddress: '192.168.1.100',
  userAgent: 'Mozilla/5.0...',
  resource: { type: 'session', id: 'session-abc' },
  action: 'authenticate',
  outcome: 'success',
  metadata: { method: 'api_key' }
});

// Log data access
await auditor.log({
  eventType: AuditEventType.CONVERSATION_READ,
  userId: 'user-123',
  ipAddress: '192.168.1.100',
  userAgent: 'Claude Code CLI/1.0',
  resource: { type: 'conversation', id: 'conv-xyz' },
  action: 'read',
  outcome: 'success',
  metadata: { messageCount: 42 }
});

// Log deletion (GDPR right to erasure)
await auditor.log({
  eventType: AuditEventType.CONVERSATION_DELETED,
  userId: 'user-123',
  ipAddress: '192.168.1.100',
  userAgent: 'Claude Code CLI/1.0',
  resource: { type: 'conversation', id: 'conv-xyz' },
  action: 'delete',
  outcome: 'success',
  metadata: { reason: 'user_request', gdpr_article: '17' }
});
```

---

## Data Privacy & Retention

### GDPR Data Minimization

```typescript
interface ConversationData {
  id: string;
  userId: string;
  messages: Message[];
  metadata: {
    createdAt: number;
    lastModified: number;
    pluginsUsed: string[];
  };
}

class GDPRCompliantStorage {
  // Data minimization: Only store what's necessary
  async storeConversation(data: ConversationData): Promise<void> {
    const minimized = {
      id: data.id,
      userId: data.userId,  // Keep for right to access
      messages: data.messages.map(m => ({
        role: m.role,
        content: this.redactPII(m.content),  // Remove PII
        timestamp: m.timestamp
      })),
      metadata: {
        createdAt: data.metadata.createdAt,
        pluginsUsed: data.metadata.pluginsUsed
        // Omit: IP addresses, user agents, detailed telemetry
      }
    };

    await db.conversations.insert(minimized);
  }

  // Redact personally identifiable information
  private redactPII(text: string): string {
    return text
      // Email addresses
      .replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, '[EMAIL_REDACTED]')
      // Phone numbers
      .replace(/\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, '[PHONE_REDACTED]')
      // SSN
      .replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[SSN_REDACTED]')
      // Credit cards
      .replace(/\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b/g, '[CC_REDACTED]');
  }
}
```

### Data Retention Policies

```typescript
enum RetentionPolicy {
  CONVERSATIONS = 90,      // 90 days
  AUDIT_LOGS = 2555,       // 7 years (SOC 2 requirement)
  ANALYTICS = 365,         // 1 year
  BACKUPS = 30             // 30 days
}

class RetentionManager {
  async enforceRetention(): Promise<void> {
    const now = Date.now();

    // Delete old conversations (GDPR: storage limitation)
    const cutoff = now - (RetentionPolicy.CONVERSATIONS * 86400000);
    await db.conversations.deleteMany({
      lastModified: { $lt: cutoff }
    });

    // Archive (not delete) audit logs
    const auditCutoff = now - (RetentionPolicy.AUDIT_LOGS * 86400000);
    const oldLogs = await db.auditLogs.find({
      timestamp: { $lt: auditCutoff }
    });
    await this.archiveToS3(oldLogs);
    await db.auditLogs.deleteMany({
      timestamp: { $lt: auditCutoff }
    });

    // Delete old analytics
    const analyticsCutoff = now - (RetentionPolicy.ANALYTICS * 86400000);
    await db.analytics.deleteMany({
      timestamp: { $lt: analyticsCutoff }
    });
  }

  private async archiveToS3(logs: any[]): Promise<void> {
    const archive = JSON.stringify(logs);
    await s3.putObject({
      Bucket: 'audit-logs-archive',
      Key: `archive-${Date.now()}.json.gz`,
      Body: gzip(archive)
    });
  }
}
```

### Right to Erasure (GDPR Article 17)

```typescript
class GDPRErasureHandler {
  async processErasureRequest(userId: string, requestId: string): Promise<void> {
    // Log the request
    await auditor.log({
      eventType: AuditEventType.DATA_EXPORT,
      userId,
      ipAddress: 'internal',
      userAgent: 'erasure-service',
      resource: { type: 'user', id: userId },
      action: 'gdpr_erasure',
      outcome: 'success',
      metadata: { requestId, article: '17' }
    });

    // Delete all user data
    await db.conversations.deleteMany({ userId });
    await db.analytics.deleteMany({ userId });
    await db.preferences.deleteMany({ userId });

    // Anonymize audit logs (can't delete due to legal requirements)
    await db.auditLogs.updateMany(
      { userId },
      { $set: { userId: `ANONYMIZED_${crypto.randomUUID()}` } }
    );

    // Generate confirmation
    await this.sendErasureConfirmation(userId, requestId);
  }

  private async sendErasureConfirmation(userId: string, requestId: string): Promise<void> {
    // Email or other notification confirming erasure
    console.log(`Erasure completed for ${userId}, request ${requestId}`);
  }
}
```

---

## Access Controls

### Role-Based Access Control (RBAC)

```typescript
enum Role {
  ADMIN = 'admin',
  DEVELOPER = 'developer',
  AUDITOR = 'auditor',
  USER = 'user'
}

enum Permission {
  CONVERSATIONS_READ = 'conversations:read',
  CONVERSATIONS_WRITE = 'conversations:write',
  CONVERSATIONS_DELETE = 'conversations:delete',
  PLUGINS_INSTALL = 'plugins:install',
  SETTINGS_MODIFY = 'settings:modify',
  AUDIT_LOGS_READ = 'audit_logs:read',
  USERS_MANAGE = 'users:manage'
}

const rolePermissions: Record<Role, Permission[]> = {
  [Role.ADMIN]: [
    Permission.CONVERSATIONS_READ,
    Permission.CONVERSATIONS_WRITE,
    Permission.CONVERSATIONS_DELETE,
    Permission.PLUGINS_INSTALL,
    Permission.SETTINGS_MODIFY,
    Permission.AUDIT_LOGS_READ,
    Permission.USERS_MANAGE
  ],
  [Role.DEVELOPER]: [
    Permission.CONVERSATIONS_READ,
    Permission.CONVERSATIONS_WRITE,
    Permission.PLUGINS_INSTALL
  ],
  [Role.AUDITOR]: [
    Permission.AUDIT_LOGS_READ,
    Permission.CONVERSATIONS_READ
  ],
  [Role.USER]: [
    Permission.CONVERSATIONS_READ,
    Permission.CONVERSATIONS_WRITE
  ]
};

class AccessControl {
  hasPermission(userRole: Role, permission: Permission): boolean {
    return rolePermissions[userRole].includes(permission);
  }

  async enforcePermission(
    userId: string,
    permission: Permission,
    action: () => Promise<void>
  ): Promise<void> {
    const user = await db.users.findOne({ id: userId });

    if (!this.hasPermission(user.role, permission)) {
      await auditor.log({
        eventType: AuditEventType.AUTHORIZATION_DENIED,
        userId,
        ipAddress: '0.0.0.0',
        userAgent: 'internal',
        resource: { type: 'permission', id: permission },
        action: 'check',
        outcome: 'failure',
        metadata: { role: user.role }
      });

      throw new Error(`Permission denied: ${permission}`);
    }

    await action();
  }
}
```

---

## SOC 2 Compliance

### SOC 2 Type II Common Criteria

**CC6: Logical and Physical Access Controls**

```typescript
// CC6.1: Access granted based on job function
class SOC2AccessControl {
  async grantAccess(userId: string, role: Role): Promise<void> {
    // Verify user identity
    const user = await this.verifyIdentity(userId);

    // Apply least privilege
    const permissions = rolePermissions[role];

    // Log access grant
    await auditor.log({
      eventType: AuditEventType.SETTINGS_CHANGED,
      userId: 'system',
      ipAddress: 'internal',
      userAgent: 'access-control',
      resource: { type: 'user', id: userId },
      action: 'grant_access',
      outcome: 'success',
      metadata: { role, permissions }
    });
  }

  // CC6.2: Access removed when no longer needed
  async revokeAccess(userId: string): Promise<void> {
    await db.users.update(
      { id: userId },
      { $set: { status: 'inactive', accessRevoked: Date.now() } }
    );

    await auditor.log({
      eventType: AuditEventType.SETTINGS_CHANGED,
      userId: 'system',
      ipAddress: 'internal',
      userAgent: 'access-control',
      resource: { type: 'user', id: userId },
      action: 'revoke_access',
      outcome: 'success',
      metadata: { reason: 'employment_termination' }
    });
  }

  // CC6.7: Detection and response to security incidents
  async detectSuspiciousActivity(userId: string): Promise<void> {
    const recentLogins = await db.auditLogs.find({
      userId,
      eventType: AuditEventType.USER_LOGIN,
      timestamp: { $gte: Date.now() - 3600000 } // Last hour
    });

    // Multiple failed logins
    const failedLogins = recentLogins.filter(l => l.outcome === 'failure');
    if (failedLogins.length >= 5) {
      await this.lockAccount(userId);
      await this.alertSecurityTeam(userId, 'brute_force_detected');
    }

    // Login from unusual location
    const locations = recentLogins.map(l => l.ipAddress);
    if (new Set(locations).size > 3) {
      await this.alertSecurityTeam(userId, 'multiple_locations');
    }
  }

  private async lockAccount(userId: string): Promise<void> {
    await db.users.update(
      { id: userId },
      { $set: { locked: true, lockedReason: 'suspicious_activity' } }
    );

    await auditor.log({
      eventType: AuditEventType.SUSPICIOUS_ACTIVITY,
      userId: 'system',
      ipAddress: 'internal',
      userAgent: 'security-monitor',
      resource: { type: 'user', id: userId },
      action: 'lock_account',
      outcome: 'success',
      metadata: { reason: 'brute_force_detected' }
    });
  }

  private async alertSecurityTeam(userId: string, reason: string): Promise<void> {
    // Send to PagerDuty, Slack, email, etc.
    console.log(`SECURITY ALERT: ${reason} for user ${userId}`);
  }

  private async verifyIdentity(userId: string): Promise<any> {
    // Multi-factor authentication check
    return await db.users.findOne({ id: userId });
  }
}
```

### SOC 2 Evidence Collection

```bash
#!/bin/bash
# collect-soc2-evidence.sh - Automated evidence gathering

EVIDENCE_DIR="/compliance/soc2/evidence-$(date +%Y-%m-%d)"
mkdir -p $EVIDENCE_DIR

# 1. Access control logs (CC6.1, CC6.2)
pg_dump -t audit_logs --data-only > $EVIDENCE_DIR/access_logs.sql

# 2. Configuration changes (CC7.2)
git log --since="30 days ago" --pretty=format:"%h %an %ad %s" \
  > $EVIDENCE_DIR/config_changes.txt

# 3. Backup verification (A1.2)
ls -lh /backups/postgres/ > $EVIDENCE_DIR/backup_verification.txt

# 4. Encryption status (CC6.6)
openssl s_client -connect claude.example.com:443 < /dev/null \
  | openssl x509 -text > $EVIDENCE_DIR/ssl_certificate.txt

# 5. Vulnerability scans (CC7.1)
docker scan ollama:latest > $EVIDENCE_DIR/vulnerability_scan.txt

echo "Evidence collected: $EVIDENCE_DIR"
```

---

## GDPR Compliance

### GDPR Articles Implementation

| Article | Requirement | Implementation |
|---------|-------------|----------------|
| **Article 6** | Lawful basis for processing | Explicit consent on signup |
| **Article 13** | Information to be provided | Privacy policy displayed |
| **Article 15** | Right of access | `/api/data-export` endpoint |
| **Article 16** | Right to rectification | User can edit profile |
| **Article 17** | Right to erasure | `/api/delete-account` endpoint |
| **Article 20** | Right to data portability | Export in JSON format |
| **Article 32** | Security of processing | Encryption at rest and in transit |

### Data Subject Rights API

```typescript
class GDPRDataSubjectRights {
  // Article 15: Right of access
  async exportUserData(userId: string): Promise<any> {
    const data = {
      profile: await db.users.findOne({ id: userId }),
      conversations: await db.conversations.find({ userId }),
      analytics: await db.analytics.find({ userId }),
      auditLogs: await db.auditLogs.find({ userId }).limit(100) // Last 100 entries
    };

    await auditor.log({
      eventType: AuditEventType.DATA_EXPORT,
      userId,
      ipAddress: 'internal',
      userAgent: 'gdpr-export-service',
      resource: { type: 'user', id: userId },
      action: 'export_data',
      outcome: 'success',
      metadata: { gdpr_article: '15' }
    });

    return data;
  }

  // Article 17: Right to erasure
  async deleteUserData(userId: string): Promise<void> {
    const erasure = new GDPRErasureHandler();
    await erasure.processErasureRequest(userId, crypto.randomUUID());
  }

  // Article 20: Right to data portability
  async exportPortableData(userId: string): Promise<string> {
    const data = await this.exportUserData(userId);

    // Export in machine-readable format (JSON)
    return JSON.stringify(data, null, 2);
  }
}
```

---

## HIPAA Compliance

### HIPAA Technical Safeguards

**PHI (Protected Health Information) must never be sent to cloud APIs**:

```typescript
class HIPAACompliantLLM {
  async processHealthcareData(patientData: any): Promise<string> {
    // ❌ HIPAA VIOLATION: Sending PHI to cloud
    // const response = await anthropic.messages.create({
    //   model: 'claude-3-5-sonnet-20241022',
    //   messages: [{ role: 'user', content: `Analyze: ${patientData}` }]
    // });

    // ✅ HIPAA COMPLIANT: Self-hosted Ollama
    const response = await fetch('http://localhost:11434/api/generate', {
      method: 'POST',
      body: JSON.stringify({
        model: 'llama3.3:70b',
        prompt: `Analyze patient data: ${patientData}`,
        stream: false
      })
    });

    const result = await response.json();

    // Audit log (required by HIPAA)
    await auditor.log({
      eventType: AuditEventType.CONVERSATION_CREATED,
      userId: 'healthcare-worker-123',
      ipAddress: '10.0.0.5',
      userAgent: 'medical-app/1.0',
      resource: { type: 'patient_analysis', id: 'patient-456' },
      action: 'process_phi',
      outcome: 'success',
      metadata: { model: 'llama3.3:70b', local: true }
    });

    return result.response;
  }
}
```

### HIPAA Business Associate Agreement (BAA)

**Self-hosted = No BAA required** (data never leaves your control)

**Required Security Controls**:
```bash
# Encryption at rest
cryptsetup luksFormat /dev/sdb
cryptsetup luksOpen /dev/sdb encrypted_volume
mkfs.ext4 /dev/mapper/encrypted_volume

# Encryption in transit (TLS 1.3 only)
openssl s_server -accept 443 -cert server.crt -key server.key \
  -tls1_3 -cipher TLS_AES_256_GCM_SHA384

# Access logging (required by HIPAA)
tail -f /var/log/audit/audit.log | grep PHI_ACCESS
```

---

## Security Hardening

### Security Checklist

```markdown
## Infrastructure Security
- [ ] All services run with least privilege (non-root users)
- [ ] Firewall configured (UFW/iptables) with default-deny
- [ ] SSH access restricted (key-only, no password auth)
- [ ] Automatic security updates enabled
- [ ] Intrusion detection system deployed (OSSEC, Fail2ban)

## Application Security
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output encoding)
- [ ] CSRF tokens on state-changing requests
- [ ] Rate limiting on APIs (429 responses)

## Data Security
- [ ] Encryption at rest (LUKS for disks)
- [ ] Encryption in transit (TLS 1.3)
- [ ] Database credentials rotated quarterly
- [ ] API keys rotated after employee departure
- [ ] Backups encrypted with separate key

## Monitoring & Response
- [ ] SIEM configured (Splunk, ELK)
- [ ] Intrusion alerts sent to security team
- [ ] Vulnerability scanning automated (weekly)
- [ ] Penetration testing scheduled (annual)
- [ ] Incident response plan documented
```

---

## Best Practices

### DO ✅

1. **Log all security events**
   ```typescript
   await auditor.log({
     eventType: AuditEventType.AUTHENTICATION_FAILED,
     userId: 'unknown',
     ipAddress,
     // ... full details
   });
   ```

2. **Encrypt sensitive data**
   ```typescript
   const encrypted = crypto.publicEncrypt(publicKey, Buffer.from(data));
   ```

3. **Implement data retention**
   ```typescript
   const retention = new RetentionManager();
   setInterval(() => retention.enforceRetention(), 86400000); // Daily
   ```

### DON'T ❌

1. **Don't store PII unnecessarily**
   ```typescript
   // ❌ Store full conversation with PII
   await db.save({ userId, messages: fullConversation });

   // ✅ Redact PII before storage
   await db.save({ userId, messages: redacted });
   ```

2. **Don't skip audit logging**
   ```typescript
   // ❌ No audit trail
   await db.conversations.delete({ id });

   // ✅ Log deletion
   await auditor.log({ eventType: 'conversation.deleted', ... });
   await db.conversations.delete({ id });
   ```

---

## Tools & Resources

### Compliance Automation

- **Vanta**: SOC 2 automation
- **Drata**: Continuous compliance
- **OneTrust**: GDPR automation
- **TrustArc**: Privacy management

### Security Scanning

- **Nessus**: Vulnerability scanning
- **OWASP ZAP**: Web app security testing
- **Trivy**: Container scanning
- **Snyk**: Dependency scanning

---

## Summary

**Key Takeaways**:

1. **Audit everything** - Immutable logs with HMAC signatures
2. **Minimize data** - GDPR requires storage limitation
3. **Self-host for HIPAA** - Cloud APIs violate PHI rules
4. **Implement RBAC** - Least privilege access
5. **Automate compliance** - Evidence collection scripts
6. **Encrypt data** - At rest and in transit
7. **Test regularly** - Penetration tests, vulnerability scans

**Compliance Checklist**:
- [ ] Audit logging implemented (immutable, signed)
- [ ] Data retention policies enforced (90-day conversations)
- [ ] GDPR rights endpoints deployed (access, erasure, portability)
- [ ] RBAC configured (admin, developer, auditor, user roles)
- [ ] SOC 2 evidence collection automated
- [ ] HIPAA PHI never sent to cloud (self-hosted Ollama only)
- [ ] Encryption enabled (TLS 1.3, LUKS disk encryption)
- [ ] Security hardening complete (firewall, SSH, updates)
- [ ] Quarterly security reviews scheduled
- [ ] Annual penetration testing planned

---

**Last Updated**: 2025-12-24
**Author**: Jeremy Longshore
**Related Playbooks**: [Self-Hosted Stack Setup](./06-self-hosted-stack.md), [MCP Server Reliability](./03-mcp-reliability.md)
