---
name: granola-reference-architecture
description: |
  Enterprise meeting workflow architecture with Granola.
  Use when designing enterprise deployments, planning integrations,
  or architecting meeting management systems.
  Trigger with phrases like "granola architecture", "granola enterprise",
  "granola system design", "meeting system", "granola infrastructure".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Granola Reference Architecture

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Enterprise reference architecture for meeting management using Granola as the core capture platform with Zapier middleware routing to Slack, Notion, CRM, and task management.

## Prerequisites
- Granola Business or Enterprise plan
- Zapier account for middleware automation
- Destination systems configured (Slack, Notion, CRM, Linear)

## Instructions

### Step 1: Set Up Core Pipeline
Meeting Platforms (Google/Zoom/Teams) -> Granola (capture/transcribe/summarize) -> Zapier (route/transform) -> Destinations (Slack, Notion, CRM, Linear)

### Step 2: Configure Data Flow Patterns
- **Standard**: Parallel notify (Slack) + archive (Notion) + create tasks (Linear)
- **Client Meeting**: Add CRM path (HubSpot note, contact update, follow-up)
- **Executive**: Private Notion, EA notification, no public Slack

### Step 3: Design Multi-Workspace Structure
Separate workspaces per department with appropriate access controls and per-workspace integrations.

### Step 4: Implement Security
Data classification (Confidential/Internal/PII), encryption (AES-256/TLS 1.3), RBAC + SSO, audit logging.

### Step 5: Plan for Scale and DR
Size workspace by team (Pro/Business/Enterprise), set performance budgets, configure nightly exports for disaster recovery.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for full architecture diagram, data flow patterns, workspace configurations, access control matrices, and disaster recovery procedures.

## Output
- Meeting ecosystem architecture documented
- Zapier routing configured per meeting type
- Multi-workspace structure deployed
- Security and DR measures in place

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Notes not routing | Zapier trigger misconfigured | Verify Granola-Zapier connection |
| Wrong destination | Filter logic error | Review Zapier filter conditions |
| Slow note delivery | Processing queue | Check Granola status page |
| Missing CRM update | External attendee not detected | Verify calendar attendee emails |

## Examples

### Performance Targets
| Metric | Target |
|--------|--------|
| Note availability | < 3 min post-meeting |
| Integration latency | < 1 min |
| Search response | < 500 ms |

## Resources
- [Granola Enterprise](https://granola.ai/enterprise)
- [Security Whitepaper](https://granola.ai/security)
- [Architecture Guide](https://granola.ai/help/architecture)

## Next Steps
Proceed to `granola-multi-env-setup` for multi-environment configuration.
