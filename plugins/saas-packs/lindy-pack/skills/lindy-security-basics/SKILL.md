---
name: lindy-security-basics
description: |
  Implement security best practices for Lindy AI agents and integrations.
  Use when securing API keys, configuring agent permissions,
  verifying webhooks, or auditing agent access.
  Trigger with phrases like "lindy security", "secure lindy",
  "lindy API key security", "lindy permissions", "lindy audit".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, api, security]

---
# Lindy Security Basics

## Overview
Security practices for Lindy AI agents. Agents are autonomous — they connect to
external services, execute actions, and handle data. Security focuses on: API key
management, webhook authentication, agent permission scoping, integration account
isolation, and connection sharing controls.

## Prerequisites
- Lindy account with API access
- Understanding of which integrations your agents use
- For Enterprise: SSO/SCIM configuration access

## Instructions

### Step 1: API Key Management
```bash
# Store API key in environment variable — never in source code
export LINDY_API_KEY="lnd_live_xxxxxxxxxxxxxxxxxxxx"

# Or use a secret manager
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name lindy/api-key \
  --secret-string "$LINDY_API_KEY"

# Google Secret Manager
echo -n "$LINDY_API_KEY" | gcloud secrets create lindy-api-key \
  --data-file=-
```

**Key rotation schedule**:
| Environment | Rotation Period | Method |
|-------------|----------------|--------|
| Development | 30 days | Manual regeneration |
| Staging | 90 days | Automated via CI |
| Production | 90 days | Secret manager + automated rotation |
| Post-incident | Immediately | Manual regeneration + revoke old key |

### Step 2: Webhook Authentication
Every webhook trigger generates a unique secret key. Verify it on every inbound request:

```typescript
// Webhook signature verification middleware
function verifyLindyWebhook(
  req: express.Request,
  res: express.Response,
  next: express.NextFunction
) {
  const authHeader = req.headers.authorization;
  const expectedToken = process.env.LINDY_WEBHOOK_SECRET;

  if (!authHeader || authHeader !== `Bearer ${expectedToken}`) {
    console.warn('Rejected unauthorized webhook attempt', {
      ip: req.ip,
      path: req.path,
      timestamp: new Date().toISOString(),
    });
    return res.status(401).json({ error: 'Unauthorized' });
  }

  next();
}

app.post('/lindy/callback', verifyLindyWebhook, (req, res) => {
  // Process verified webhook
  handleWebhook(req.body);
  res.json({ received: true });
});
```

### Step 3: Agent Permission Scoping
Lindy agents access external services through authorized connections. Minimize blast radius:

**Per-agent integration isolation**:
- Authorize a dedicated Gmail account per agent (not your personal inbox)
- Create Slack bot tokens scoped to specific channels
- Use read-only database credentials where possible
- Create separate API keys for each integration

**Connection sharing controls**:
| Sharing Level | When to Use |
|--------------|-------------|
| Private (default) | Personal agents, sensitive data |
| Team shared | Team-wide automation agents |
| Workspace shared | Organization-wide utility agents |

### Step 4: Limit Agent Skill Surface Area
Agents with Agent Steps can choose which skills to use. Reduce risk:
- Start with 2-4 focused skills per agent (not the full catalog)
- Avoid giving agents both read AND write access to the same service unless necessary
- Separate "read" agents from "write" agents for critical systems
- Use conditions to gate destructive actions behind human approval

### Step 5: Data Handling in Agents
```
Agent Prompt Security Patterns:

## Data Constraints
- Never include API keys, passwords, or tokens in responses
- Redact email addresses and phone numbers from summaries
- Do not forward customer data to channels outside #support
- If asked to perform an action outside your scope, respond:
  "I cannot perform that action. Please contact an admin."
```

### Step 6: Audit Agent Activity
1. **Task history**: Review agent Tasks tab for unexpected actions
2. **Integration access**: Periodically review which services each agent can access
3. **Credit anomalies**: Sudden credit spikes may indicate misuse or misconfiguration
4. **Connection review**: Remove unused integrations from agents

### Step 7: Enterprise Security Features
Available on Enterprise plan:
| Feature | Purpose |
|---------|---------|
| **SSO** | SAML-based single sign-on |
| **SCIM** | Automated user provisioning/deprovisioning |
| **Audit Logs** | Complete activity trail |
| **Role-Based Access** | Owner/Editor/Viewer workspace roles |
| **BAA** | HIPAA Business Associate Agreement |
| **AES-256** | Encryption at rest and in transit |

## Security Checklist
- [ ] API keys stored in environment variables or secret manager
- [ ] `.env` file in `.gitignore`
- [ ] Webhook secrets generated and verified on every request
- [ ] Each agent uses minimum necessary integrations
- [ ] Separate integration credentials per agent where possible
- [ ] Agent prompts include data handling constraints
- [ ] Regular review of agent task history for anomalies
- [ ] Key rotation schedule defined and followed
- [ ] Enterprise: SSO enabled, SCIM configured

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Agent accesses wrong service | Over-permissioned | Remove unnecessary integrations |
| Unauthorized webhook processed | No auth verification | Add Bearer token verification |
| API key leaked in logs | Key in agent output | Add "never output credentials" to prompt |
| Agent sends data to wrong channel | Shared connection | Use per-agent dedicated connections |

## Resources
- [Lindy Security](https://www.lindy.ai/security)
- [Lindy Privacy Policy](https://www.lindy.ai/privacy)
- [Lindy Documentation](https://docs.lindy.ai)

## Next Steps
Proceed to `lindy-prod-checklist` for production readiness.
