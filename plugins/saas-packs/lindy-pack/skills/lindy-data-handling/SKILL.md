---
name: lindy-data-handling
description: |
  Data handling best practices for Lindy AI agents.
  Use when managing sensitive data in agent workflows,
  implementing data privacy controls, or ensuring compliance.
  Trigger with phrases like "lindy data", "lindy privacy",
  "lindy PII", "lindy data handling", "lindy GDPR", "lindy HIPAA".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, compliance]

---
# Lindy Data Handling

## Overview
Lindy agents process data through triggers, LLM calls, actions, knowledge bases,
and memory. Data flows through Lindy's managed infrastructure with AES-256
encryption at rest and in transit. This skill covers data classification, PII
handling, prompt-level data controls, and regulatory compliance.

## Prerequisites
- Understanding of data types processed by your agents
- Knowledge of applicable regulations (GDPR, CCPA, HIPAA)
- For HIPAA: Business Associate Agreement (BAA) with Lindy (Enterprise plan)

## Lindy Data Architecture

| Component | Data Storage | Retention |
|-----------|-------------|-----------|
| **Tasks** | Task inputs, outputs, step data | Visible in dashboard |
| **Memory** | Persistent snippets across tasks | Until manually deleted |
| **Context** | Per-task accumulated context | Task lifetime only |
| **Knowledge Base** | Uploaded files, crawled sites | Until manually removed |
| **Integrations** | OAuth tokens, connection data | Until disconnected |
| **Computer Use** | Browser session, screenshots | 30 days after last use |

## Instructions

### Step 1: Classify Data in Agent Workflows
Map what data each agent processes:

| Data Category | Examples | Handling |
|--------------|---------|----------|
| **Public** | Product info, FAQs, pricing | No restrictions |
| **Internal** | Sales reports, meeting notes | Limit to authorized agents |
| **Confidential** | Customer emails, CRM data | Access controls + audit |
| **Restricted** | PII, PHI, payment data | Minimize exposure + compliance |

### Step 2: PII Controls in Agent Prompts
Add data handling instructions directly to agent prompts:
```
## Data Handling Rules
- Never include full email addresses in summaries — use "[name]@[domain]"
- Redact phone numbers in logs — show only last 4 digits
- Do not forward customer personal information to Slack channels
- When storing to spreadsheet, omit columns: email, phone, address
- If asked to share customer data externally, decline and escalate
```

### Step 3: Knowledge Base Data Safety
Knowledge base files are searchable by the agent. Control what goes in:

**DO upload**:
- Product documentation
- FAQ articles
- Policy documents
- Public knowledge articles

**DO NOT upload**:
- Customer databases with PII
- Credentials or API keys
- Internal HR documents (unless agent specifically needs them)
- Financial records with account numbers

**Resync considerations**: KB auto-refreshes every 24 hours. If you upload
sensitive content by mistake, remove it AND trigger a manual Resync.

### Step 4: Secure Memory Usage
Agent memories persist across all future tasks. Be deliberate:
```
Safe memory: "Customer prefers email communication over phone"
Safe memory: "Billing questions should escalate to finance@company.com"

Risky memory: "John Smith's SSN is 123-45-6789"  ← NEVER store PII in memory
Risky memory: "API key for Stripe: sk_live_xxxx"  ← NEVER store secrets
```

Add to agent prompt:
```
## Memory Rules
- Never store personally identifiable information (PII) in memory
- Never store credentials, API keys, or passwords in memory
- Memories should contain preferences, patterns, and procedures only
```

### Step 5: Computer Use Data Isolation
If using Computer Use (browser automation):
- Sessions persist for 30 days with saved credentials
- Enable **Incognito mode** for sessions handling sensitive data
- Use **dedicated** (not shared) computer assignments for sensitive agents
- Review screenshots captured during execution for data exposure

### Step 6: Integration Account Isolation
- Authorize dedicated service accounts per agent (not personal accounts)
- Use Gmail with a team alias, not an individual inbox
- Create read-only database credentials where possible
- Revoke access immediately when an agent is decommissioned

### Step 7: Regulatory Compliance

**GDPR (EU Data Protection)**:
- [ ] Document what personal data each agent processes
- [ ] Ensure agents only process data with valid legal basis
- [ ] Implement data subject access/deletion capabilities
- [ ] Agent prompt includes "do not retain personal data beyond task completion"
- [ ] Review Lindy's data processing agreement

**CCPA (California Consumer Privacy)**:
- [ ] Identify agents processing California resident data
- [ ] Ensure opt-out mechanisms exist for data processing
- [ ] Agent prompt prevents selling/sharing personal information

**HIPAA (Healthcare)**:
- [ ] Enterprise plan with BAA in place
- [ ] Agents only access minimum necessary PHI
- [ ] No PHI in agent memory or knowledge base
- [ ] Audit trail enabled for all PHI access
- [ ] Agent prompt includes PHI handling restrictions

### Step 8: Data Retention Management
```
Agent Prompt Addition:
## Data Retention
- Do not reference data from tasks older than 30 days
- Clear task context after each run (do not accumulate indefinitely)
- When updating memory, remove outdated entries
- Summarize customer interactions, do not store verbatim transcripts
```

## Data Handling Checklist
- [ ] Each agent's data classification documented
- [ ] PII handling rules in every agent prompt
- [ ] Knowledge base audited for sensitive content
- [ ] Memory creation restricted (no PII, no secrets)
- [ ] Integration accounts isolated per agent
- [ ] Computer Use sessions set to dedicated + incognito where needed
- [ ] Regulatory compliance requirements mapped
- [ ] BAA in place if handling healthcare data
- [ ] Data retention policy defined and enforced in prompts

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| PII in Slack channel | Agent forwarded customer email | Add "never forward PII to Slack" to prompt |
| Sensitive file in KB | Uploaded by mistake | Remove file + trigger KB resync immediately |
| Memory contains PII | Agent auto-created memory | Delete memory + add "never store PII" to prompt |
| Audit finding | Agent accessing unnecessary data | Remove unused integrations from agent |

## Resources
- [Lindy Security](https://www.lindy.ai/security)
- [Lindy Privacy Policy](https://www.lindy.ai/privacy)
- [GDPR Official](https://gdpr.eu/)
- [Lindy Documentation](https://docs.lindy.ai)

## Next Steps
Proceed to `lindy-enterprise-rbac` for access control.
