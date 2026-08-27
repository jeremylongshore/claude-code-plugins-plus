---
name: fathom-reference-architecture
description: 'Reference architecture for Fathom meeting intelligence integrations.

  Trigger with phrases like "fathom architecture", "fathom design", "fathom integration
  pattern".

  '
allowed-tools: Read, Grep
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- meeting-intelligence
- ai-notes
- fathom
compatibility: Designed for Claude Code
---
# Fathom Reference Architecture

## Overview

Define meeting ingestion, consent, Fathom processing, CRM/follow-up integration, redacted observability, retention, and incident boundaries as an owned system.

## Prerequisites

- A documented data/consent model, environment boundaries, integration owners, and approved data-retention policy.

## Instructions

1. Map meeting sources, identities, processing, integrations, access, and audit paths to owners.
2. Separate development/staging/production credentials and use role-limited access at every boundary.
3. Build idempotent integrations and fallback/rollback decisions before production automation.

## Output

- An architecture record with trust boundaries, ownership, consent/data controls, and reversible integration points.

## Error Handling

| Condition | Safe response |
|---|---|
| CRM or follow-up integration fails | Pause the affected automation and use the documented reconciliation path. |
| Access boundary is unclear | Use the restrictive setting and escalate to the data/tenant owner. |
| Meeting content is exposed | Restrict access and follow the incident procedure. |

## Examples

Model a development flow from a synthetic meeting to a scoped Fathom integration and test CRM record, retaining only opaque correlation/audit metadata. Promote the reviewed version through staging before a production canary; do not make summary output an unreviewed system of record.

## Architecture

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  Fathom AI   │────▶│  Webhook        │────▶│  Meeting DB      │
│  (Recordings)│     │  Handler        │     │  (PostgreSQL)    │
└──────────────┘     └─────────────────┘     └────────┬─────────┘
                                                       │
                     ┌─────────────────┐     ┌────────▼─────────┐
                     │  Action Item    │     │  CRM Sync        │
                     │  Extractor      │────▶│  (Salesforce/    │
                     └─────────────────┘     │   HubSpot)       │
                            │                └──────────────────┘
                     ┌──────▼──────────┐
                     │  Follow-up      │
                     │  Email Sender   │
                     └─────────────────┘
```

## Project Structure

```
fathom-platform/
├── src/
│   ├── fathom_client.py
│   ├── webhook_handler.py
│   ├── transcript_processor.py
│   ├── action_extractor.py
│   ├── crm_sync.py
│   └── email_sender.py
├── sql/
│   └── schema.sql
├── tests/
│   ├── fixtures/
│   └── test_processor.py
└── deploy/
    ├── cloud-function/
    └── docker-compose.yaml
```

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Data delivery | Webhooks | Real-time, no polling |
| Storage | PostgreSQL | Structured meeting data |
| Processing | Cloud Function | Serverless, scales with meeting volume |
| CRM sync | Async queue | Handles CRM rate limits |

## Resources

- [Fathom API Docs](https://developers.fathom.ai)
- [Fathom Webhooks](https://developers.fathom.ai/webhooks)

## Next Steps

This completes the Fathom skill pack. Start with `fathom-install-auth`.
