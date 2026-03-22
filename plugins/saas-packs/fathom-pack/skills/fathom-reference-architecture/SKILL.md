---
name: fathom-reference-architecture
description: |
  Reference architecture for Fathom meeting intelligence integrations.
  Trigger with phrases like "fathom architecture", "fathom design", "fathom integration pattern".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom Reference Architecture

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
