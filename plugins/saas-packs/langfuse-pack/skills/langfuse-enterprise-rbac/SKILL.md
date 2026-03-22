---
name: langfuse-enterprise-rbac
description: |
  Configure Langfuse enterprise organization management and access control.
  Use when implementing team access controls, configuring organization settings,
  or setting up role-based permissions for Langfuse projects.
  Trigger with phrases like "langfuse RBAC", "langfuse teams",
  "langfuse organization", "langfuse access control", "langfuse permissions".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langfuse, rbac]

---
# Langfuse Enterprise RBAC

## Overview
Configure enterprise access control for Langfuse: built-in roles and permissions, scoped API keys per service, SSO integration, project-level isolation, and audit logging for compliance.

## Prerequisites
- Langfuse Cloud (Team/Enterprise plan) or self-hosted instance
- Organization admin access
- SSO provider (optional, for SAML/OIDC integration)

## Langfuse Built-In Roles

Langfuse provides these roles at the project level:

| Role | View Traces | Create Traces | Manage Prompts | Manage Members | Manage Billing |
|------|------------|---------------|----------------|----------------|---------------|
| **Owner** | Yes | Yes | Yes | Yes | Yes |
| **Admin** | Yes | Yes | Yes | Yes | No |
| **Member** | Yes | Yes | Yes | No | No |
| **Viewer** | Yes | No | No | No | No |

## Instructions

### Step 1: Organization and Project Structure

```
Organization: Acme Corp
├── Project: production-chatbot
│   ├── Owner: engineering-lead@acme.com
│   ├── Admin: senior-dev@acme.com
│   ├── Member: developer@acme.com
│   └── API Key: sk-lf-prod-chatbot-...
│
├── Project: staging-chatbot
│   ├── Admin: senior-dev@acme.com
│   ├── Member: developer@acme.com
│   └── API Key: sk-lf-staging-chatbot-...
│
└── Project: analytics-readonly
    ├── Admin: data-lead@acme.com
    ├── Viewer: analyst@acme.com
    └── API Key: sk-lf-analytics-...
```

**Best practice:** Separate projects for production, staging, and analytics. Never share API keys across environments.

### Step 2: Scoped API Keys

Create API keys with specific purposes and rotate regularly:

```typescript
// In Langfuse UI: Settings > API Keys > Create
// Each key pair (public + secret) is scoped to one project

// Service-specific keys
// Backend API:     pk-lf-prod-api-...  / sk-lf-prod-api-...
// CI/CD pipeline:  pk-lf-ci-...       / sk-lf-ci-...
// Analytics:       pk-lf-analytics-... / sk-lf-analytics-...

// Validate key scope at startup
function validateApiKeyScope(expectedProject: string) {
  const pk = process.env.LANGFUSE_PUBLIC_KEY || "";

  if (!pk.includes(expectedProject)) {
    console.warn(
      `WARNING: API key may not match expected project: ${expectedProject}`
    );
  }
}

// Key rotation script
async function rotateApiKeys() {
  // 1. Create new key pair in Langfuse UI
  // 2. Deploy new keys to secret manager
  // 3. Wait for all instances to pick up new keys
  // 4. Revoke old key pair in Langfuse UI

  console.log("Key rotation checklist:");
  console.log("1. [ ] New key pair created in Langfuse");
  console.log("2. [ ] New keys deployed to secret manager");
  console.log("3. [ ] All services restarted with new keys");
  console.log("4. [ ] Old key pair revoked in Langfuse");
  console.log("5. [ ] Verified traces flowing with new keys");
}
```

### Step 3: Self-Hosted Access Control

```yaml
# docker-compose.yml -- enterprise hardening
services:
  langfuse:
    image: langfuse/langfuse:latest
    environment:
      # Disable public registration
      - AUTH_DISABLE_SIGNUP=true

      # SSO enforcement for your domain
      - AUTH_DOMAINS_WITH_SSO_ENFORCEMENT=acme.com

      # Default role for new project members
      - LANGFUSE_DEFAULT_PROJECT_ROLE=VIEWER

      # Encrypt data at rest
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}

      # Session security
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
```

### Step 4: SSO Integration

**SAML Setup (Okta, Azure AD, OneLogin):**

1. In your IdP, create a new SAML application for Langfuse
2. Configure the SSO callback URL: `https://langfuse.your-domain.com/api/auth/callback/saml`
3. Set the entity ID: `https://langfuse.your-domain.com`
4. Map IdP groups to Langfuse roles:

```yaml
# Self-hosted SSO configuration
services:
  langfuse:
    environment:
      - AUTH_CUSTOM_CLIENT_ID=${SAML_CLIENT_ID}
      - AUTH_CUSTOM_CLIENT_SECRET=${SAML_CLIENT_SECRET}
      - AUTH_CUSTOM_ISSUER=https://your-idp.com/saml
      - AUTH_DOMAINS_WITH_SSO_ENFORCEMENT=acme.com
```

### Step 5: Audit Logging

Track access and permission changes for compliance:

```typescript
// Application-level audit logging for Langfuse operations
import { LangfuseClient } from "@langfuse/client";

interface AuditEvent {
  timestamp: string;
  actor: string;
  action: string;
  resource: string;
  details: Record<string, any>;
}

const auditLog: AuditEvent[] = [];

function logAuditEvent(event: Omit<AuditEvent, "timestamp">) {
  const entry: AuditEvent = {
    ...event,
    timestamp: new Date().toISOString(),
  };
  auditLog.push(entry);
  console.log(`[AUDIT] ${entry.action}: ${entry.resource} by ${entry.actor}`);

  // In production: send to your SIEM or audit log service
  // await sendToSIEM(entry);
}

// Audit Langfuse API key usage
function auditedLangfuseClient(actor: string): LangfuseClient {
  const client = new LangfuseClient();

  // Log score creation
  const originalScoreCreate = client.score.create.bind(client.score);
  client.score.create = async (params) => {
    logAuditEvent({
      actor,
      action: "score.create",
      resource: `trace:${params.traceId}`,
      details: { scoreName: params.name },
    });
    return originalScoreCreate(params);
  };

  return client;
}
```

## Access Control Checklist

| Category | Requirement | Implementation |
|----------|------------|----------------|
| Authentication | SSO enforced for org domain | `AUTH_DOMAINS_WITH_SSO_ENFORCEMENT` |
| Registration | Public signup disabled | `AUTH_DISABLE_SIGNUP=true` |
| Default role | Least privilege | `LANGFUSE_DEFAULT_PROJECT_ROLE=VIEWER` |
| API keys | Per-service, per-environment | Separate keys in secret manager |
| Key rotation | Quarterly or on compromise | Documented rotation procedure |
| Data encryption | At-rest encryption | `ENCRYPTION_KEY` configured |
| Audit trail | All access logged | Application-level audit logging |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Permission denied | Insufficient role | Request role upgrade from project owner |
| SSO login fails | Wrong callback URL | Verify SAML callback URL matches |
| API key rejected | Wrong project or revoked | Create new key pair for correct project |
| New user gets no access | Not added to project | Admin must invite to specific project |

## Resources
- [Langfuse Access Control](https://langfuse.com/docs/rbac)
- [Self-Hosting Configuration](https://langfuse.com/self-hosting/configuration)
- [Headless Initialization](https://langfuse.com/self-hosting/administration/headless-initialization)
