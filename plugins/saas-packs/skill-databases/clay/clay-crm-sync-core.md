# clay-crm-sync-core

## File Scaffold

```
clay-crm-sync-core/
|-- SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Implement the core Clay workflow: CRM synchronization with bidirectional data flow. Connects Clay to Salesforce, HubSpot, or other CRMs with enrichment triggers and automated updates.
**Workflow:** Integration workflow skill. Use when setting up Clay as the enrichment layer for CRM data.
**Relates to:** Builds on clay-enrichment-patterns; integrates with clay-webhooks-events for real-time updates.

## Summary

This skill implements bidirectional CRM synchronization with Clay. It covers configuring connections to major CRMs (Salesforce, HubSpot, Pipedrive), setting up enrichment triggers on new or updated records, implementing bidirectional data flow, and configuring field mappings. This enables automated prospect enrichment as part of the sales workflow.
