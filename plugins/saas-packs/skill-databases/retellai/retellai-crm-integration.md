# retellai-crm-integration

> Integrate Retell AI with CRM systems like Salesforce, HubSpot, and Pipedrive for call logging and contact sync

## Directory Structure

```
retellai-crm-integration/
├── SKILL.md
└── examples/
    └── example.py
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for CRM integration |
| examples/example.py | Python | Example CRM sync workflows for Salesforce and HubSpot |

## Summary

**Category:** advanced
**Target Audience:** Integration engineers, Sales ops, Backend developers
**Trigger Phrases:** `retell CRM`, `retell Salesforce`, `retell HubSpot`, `retell integration`, `retell call logging`

### What This Skill Does

This skill integrates Retell AI with popular CRM systems for unified customer data. It covers logging calls to Salesforce, HubSpot, or Pipedrive, syncing contact information from CRM to personalize calls, triggering automation workflows based on call outcomes, storing transcripts and summaries in CRM records, and maintaining data consistency across systems.

### Technical Success Criteria

- CRM integration active and authenticated
- Call logs syncing to CRM records
- Contact data flowing from CRM to agent
- Automation triggers configured for call outcomes
- Error handling for sync failures

### Business Success Criteria

- Unified customer data across voice and CRM
- Improved sales efficiency with context
- 100% call data synced to CRM within 5 minutes of call completion

## Related Skills

- retellai-webhooks-events - Triggering CRM updates
- retellai-call-analytics - Data enrichment before sync
- retellai-custom-llm - CRM-aware agent responses
