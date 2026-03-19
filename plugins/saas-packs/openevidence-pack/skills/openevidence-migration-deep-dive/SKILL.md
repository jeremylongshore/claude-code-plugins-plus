---
name: openevidence-migration-deep-dive
description: |
  Execute complex OpenEvidence migrations including EHR integration, data migration, and system transitions.
  Use when migrating from legacy clinical decision support systems, integrating with new EHRs,
  or performing major platform transitions.
  Trigger with phrases like "openevidence migration", "ehr integration",
  "migrate to openevidence", "clinical ai migration", "legacy cds migration".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenEvidence Migration Deep Dive

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Execute complex migrations including legacy CDS system transitions, EHR integrations (Epic/Cerner), and multi-site deployments for OpenEvidence clinical AI.

## Prerequisites
- Access to both source and target systems
- Downtime window approved (if required)
- Rollback plan documented
- Clinical staff communication plan

## Migration Scenarios

| Scenario | Complexity | Downtime | Duration |
|----------|------------|----------|----------|
| Legacy CDS to OpenEvidence | High | 4-8 hours | 2-4 weeks |
| Add EHR Integration | Medium | None | 1-2 weeks |
| Multi-site Expansion | Medium | None | 1-2 weeks |
| API Version Upgrade | Low | None | 1-3 days |

## Instructions

### Step 1: Assess Legacy System
Audit current usage (daily queries, peak rate, unique users), map features, identify integrations (EHR, SSO, audit), and determine data migration scope (saved searches, preferences, audit logs -- required for HIPAA).

### Step 2: Implement Parallel Running
Create `ParallelRunner` that queries OpenEvidence as primary, optionally queries legacy for comparison (configurable ratio). Log comparison metrics (response time, confidence, citation count) without PHI. Auto-fallback to legacy on OpenEvidence failure.

### Step 3: Migrate Data
Run migration jobs for users (with role mapping), user preferences, and audit logs (HIPAA required). Use upsert for idempotency, batch processing for audit logs (10k per batch), and progress tracking.

### Step 4: Integrate with EHR (Epic/Cerner)
Configure SMART on FHIR with appropriate scopes. Implement CDS Hooks endpoints for `patient-view` and `medication-prescribe`. Extract conditions and medications from FHIR prefetch data for OpenEvidence queries.

### Step 5: Configure Multi-Site
Define per-site configuration: siteId, region, OpenEvidence orgId, EHR system, feature flags, and quotas. Support different tiers per site.

### Step 6: Execute Cutover
Follow migration checklist: pre-migration (approvals, backups, test env), during (parallel run, data migration, EHR testing), post (decommission legacy, train staff, document lessons).

## Output
- Legacy system assessment and feature mapping
- Parallel running with comparison metrics
- Data migration scripts (users, preferences, audit logs)
- EHR integration (SMART on FHIR, CDS Hooks)
- Multi-site configuration
- Migration checklist

## Error Handling
| Migration Issue | Detection | Resolution |
|-----------------|-----------|------------|
| Data corruption | Validation checks | Restore from backup |
| SSO failure | Auth errors | Verify IdP configuration |
| EHR integration fails | CDS Hook errors | Check FHIR endpoints |
| Performance regression | Metrics comparison | Optimize or rollback |

## Examples

### CDS Hook Discovery
```json
{
  "services": [
    { "id": "openevidence-clinical-decision-support", "hook": "patient-view" },
    { "id": "openevidence-drug-interaction", "hook": "medication-prescribe" }
  ]
}
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [SMART on FHIR](https://smarthealthit.org/)
- [CDS Hooks](https://cds-hooks.hl7.org/)
- [Epic App Orchard](https://appmarket.epic.com/)