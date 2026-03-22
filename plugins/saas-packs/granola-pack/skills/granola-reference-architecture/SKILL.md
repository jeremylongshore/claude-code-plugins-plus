---
name: granola-reference-architecture
description: |
  Enterprise reference architecture for meeting management with Granola.
  Use when designing org-wide meeting workflows, planning integration topology,
  or architecting meeting-to-action pipelines across departments.
  Trigger: "granola architecture", "granola enterprise design",
  "granola system design", "meeting system architecture".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, architecture, enterprise]

---
# Granola Reference Architecture

## Overview
Enterprise reference architecture for deploying Granola as the meeting intelligence platform across an organization. Covers the core capture pipeline, Zapier middleware routing, multi-workspace topology, security layers, and integration patterns for Slack, Notion, CRM, and task management.

## Prerequisites
- Granola Enterprise plan ($35+/user/month)
- Zapier Professional or higher (for multi-step Zaps and Paths)
- Destination systems provisioned (Slack, Notion, CRM, Linear/Jira)
- IT architecture review completed

## Instructions

### Step 1 — Core Pipeline Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MEETING PLATFORMS                      │
│  Zoom  |  Google Meet  |  Microsoft Teams  |  Slack Huddle│
└──────────────────────┬──────────────────────────────────┘
                       │ System audio capture (no bot)
                       ▼
┌─────────────────────────────────────────────────────────┐
│                    GRANOLA PLATFORM                       │
│                                                          │
│  ┌──────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │ Audio    │→ │ Transcription │→ │ AI Enhancement  │   │
│  │ Capture  │  │ (GPT-4o/     │  │ (Notes + Trans- │   │
│  │ (local)  │  │  Claude)     │  │  cript merge)   │   │
│  └──────────┘  └──────────────┘  └────────┬────────┘   │
│                                            │             │
│  ┌────────────────┐  ┌──────────────────┐  │            │
│  │ People &       │  │ Folders          │  │            │
│  │ Companies      │  │ (routing rules)  │←─┘            │
│  │ (built-in CRM) │  └────────┬─────────┘              │
│  └────────────────┘           │                         │
└───────────────────────────────┼─────────────────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │           ZAPIER MIDDLEWARE            │
            │                                       │
            │  ┌─────────┐  ┌─────────┐  ┌──────┐ │
            │  │ Filter  │→ │ Route   │→ │ Act  │ │
            │  │ (type/  │  │ (paths  │  │      │ │
            │  │ attendee)│  │ /rules) │  │      │ │
            │  └─────────┘  └─────────┘  └──────┘ │
            └──────┬──────────┬──────────┬─────────┘
                   │          │          │
        ┌──────────┴──┐ ┌────┴────┐ ┌───┴────────┐
        │ COMMUNICATE │ │ ARCHIVE │ │ ACT        │
        │ Slack       │ │ Notion  │ │ Linear/Jira│
        │ Email       │ │ Drive   │ │ Asana      │
        │ Teams       │ │ GCS/S3  │ │ HubSpot    │
        └─────────────┘ └─────────┘ └────────────┘
```

### Step 2 — Folder-Based Routing Topology

Design folder structure to drive automated routing:

| Folder | Trigger Type | Destinations | Permissions |
|--------|-------------|-------------|-------------|
| `Sales / Discovery` | Auto | Slack #sales + HubSpot Deal + Follow-up Email | Sales team |
| `Sales / Demo` | Auto | Slack #sales + HubSpot Contact | Sales team |
| `Engineering / Sprint` | Auto | Slack #eng + Linear tasks + Notion wiki | Engineering |
| `Engineering / Architecture` | Auto | Slack #eng-arch + Notion ADR database | Senior engineers |
| `Product / Customer Feedback` | Auto | Slack #product + Notion feedback DB | Product team |
| `Leadership / All-Hands` | Auto | Slack #general + Google Drive archive | All |
| `Leadership / Board` | Manual only | Private Notion, no Slack | Executives only |
| `HR / Interviews` | Manual share | Greenhouse scorecard | Hiring managers |
| `HR / 1-on-1s` | None | Private, no automation | Individual |

### Step 3 — Multi-Workspace Topology

```
Organization (Enterprise)
├── Engineering Workspace
│   ├── Folders: Sprint, Architecture, Standup, Retro
│   ├── Integrations: Linear, Notion, Slack #engineering
│   └── Retention: 2 years notes, 90 days transcripts
│
├── Sales Workspace
│   ├── Folders: Discovery, Demo, Pipeline Review
│   ├── Integrations: HubSpot, Slack #sales, Gmail
│   └── Retention: 1 year notes, 90 days transcripts
│
├── Product Workspace
│   ├── Folders: Customer Feedback, Design Review, PRD
│   ├── Integrations: Notion, Linear, Slack #product
│   └── Retention: 2 years notes, 90 days transcripts
│
├── HR Workspace (Confidential)
│   ├── Folders: Interviews, 1-on-1s, Performance
│   ├── Integrations: Greenhouse (via Zapier)
│   ├── Retention: 30 days notes, 7 days transcripts
│   └── Restrictions: No external sharing, MFA required
│
└── Executive Workspace (Confidential)
    ├── Folders: Board, Strategy, M&A
    ├── Integrations: Private Notion only
    ├── Retention: Custom (legal hold capable)
    └── Restrictions: IP allowlist, 4-hour session timeout
```

### Step 4 — Security Architecture

```
Authentication Layer:
  SSO (Okta/Azure AD) → SCIM provisioning → JIT workspace assignment

Data Protection:
  In Transit: TLS 1.3 (all API calls)
  At Rest: AES-256 (server-side storage)
  Local: FileVault/BitLocker (cache-v3.json encryption)

Access Control:
  Org Owner → Workspace Admin → Team Lead → Member → Viewer → Guest
  ↓
  SSO groups mapped to Granola roles per workspace

Data Classification:
  Confidential: HR, Legal, Board (restricted sharing, short retention)
  Internal: Engineering, Product (team sharing, standard retention)
  External-Facing: Sales, Customer Success (CRM sync allowed)

Compliance:
  SOC 2 Type 2: Certified (July 2025)
  GDPR: DPA available, data export/deletion supported
  AI Training: Opt-out enforced org-wide (Enterprise default)
```

### Step 5 — Integration Data Flow Patterns

**Pattern A: Standard Meeting (Parallel)**
```
Note enhanced → Folder trigger fires
  ├─→ Slack notification (immediate)
  ├─→ Notion archive (immediate)
  └─→ Linear tasks (per action item)
```

**Pattern B: Sales Meeting (Sequential)**
```
Note enhanced → "Sales / Discovery" folder
  │
  ├─→ HubSpot: Find Contact by attendee email
  │     ├─→ Found: Log meeting note on Contact
  │     └─→ Not found: Create Contact, then log note
  │
  ├─→ ChatGPT: Generate BANT analysis + follow-up email
  │     └─→ Gmail: Create draft to external attendees
  │
  └─→ Slack: Post summary to #sales with deal context
```

**Pattern C: Executive Meeting (Restricted)**
```
Note enhanced → "Board" folder (no auto-trigger)
  │
  └─→ Manual share to private Notion database only
       └─→ Link expires in 7 days
```

### Step 6 — Disaster Recovery & Data Export

```
Backup Strategy:
  Primary: Granola cloud storage (server-side, encrypted)
  Secondary: Local cache (cache-v3.json on each user's device)
  Tertiary: Nightly export to cloud storage (via Zapier + GCS/S3)

Recovery Procedures:
  1. User device loss: Re-authenticate, data syncs from server
  2. Integration outage: Zapier retries automatically; monitor Zap history
  3. Granola service outage: Manual notes during outage; capture resumes on recovery
  4. Data export request: Enterprise API bulk export or per-user Settings > Data > Export
```

## Output
- Complete meeting ecosystem architecture documented
- Folder-based routing configured per department
- Multi-workspace topology deployed with appropriate isolation
- Security and compliance controls mapped to org requirements
- Disaster recovery plan established

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Notes routing to wrong destination | Filter logic error in Zapier Paths | Review path conditions, test with sample data |
| Cross-workspace access denied | Permission boundaries working correctly | Elevate user role or add to target workspace |
| Integration sync delay > 5 min | Zapier queue or destination rate limit | Add delay step, check destination API limits |
| Missing CRM updates for new contacts | Native integration doesn't auto-create | Add Zapier "Find or Create" step |
| Audit log gaps | Logging not enabled on workspace | Enable in Workspace Settings > Security |

## Resources
- [Granola Enterprise](https://www.granola.ai/security)
- [Integrations Overview](https://docs.granola.ai/help-center/sharing/integrations/integrations-with-granola)
- [Enterprise API](https://docs.granola.ai/help-center/sharing/integrations/enterprise-api)
- [Security Standards](https://docs.granola.ai/help-center/consent-security-privacy/our-security-standards)

## Next Steps
Proceed to `granola-multi-env-setup` for workspace creation and configuration.
