---
name: juicebox-migration-deep-dive
description: 'Migrate to Juicebox from other tools.

  Trigger: "switch to juicebox", "migrate to juicebox".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.16.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- recruiting
- juicebox
compatibility: Designed for Claude Code
---
# Juicebox Migration Deep Dive

## Comparison

| Feature | LinkedIn Recruiter | Juicebox |
|---------|-------------------|----------|
| Search | Boolean only | Natural language (PeopleGPT) |
| Contact data | InMail only | Email + phone |
| ATS integration | Limited | 41+ systems |
| AI features | Basic | AI Skills Map, research profiles |

## Migration Steps

1. Export saved searches from current tool
2. Translate boolean queries to natural language
3. Re-create talent pools in Juicebox
4. Configure ATS integration
5. Set up outreach sequences

## Query Translation

```
# Boolean: ("software engineer" OR "SWE") AND "Python" AND "San Francisco"
# PeopleGPT: software engineer with Python experience in San Francisco
```

## Overview

This migration workflow moves approved enrichment configurations without treating contact records as transferable test data. Every cohort retains source authority, suppression, retention, destination, and rollback boundaries.

## Prerequisites

- A signed migration plan with data owners, source-authority and suppression policies, synthetic fixtures, approved destination, and cutover/rollback owner.

## Instructions

1. Baseline source authority, aggregate counts, suppression state, retention, destination scope, and synthetic probe outcomes before migration.
2. Rehearse a bounded idempotent migration in sandbox; quarantine unknown sources, schema mismatches, and unverified records.
3. Migrate one approved cohort at a time, compare aggregate counts/policy probes, and retain opaque correlation IDs only.
4. Cut over after owner approval and an observation window; keep the prior configuration available until recovery criteria are met.
5. Roll back for source, destination, suppression, integrity, or retention failure and delete staged artifacts before retrying.

## Output

Create a migration receipt with cohort, baseline/target counts, source/destination/suppression results, checkpoint, owner approval, cutover status, retention/deletion action, and rollback reference. Never attach contact details or credentials.

## Error Handling

Stop on unknown authority, destination, suppression state, incomplete deletion, or non-idempotent replay. Restore the prior controlled path and escalate with redacted evidence rather than forcing cutover.

## Examples

`cohort=synthetic-prospects-01; baseline=420; migrated=420; source=approved; suppression=pass; contacts_exported=0; cutover=held; rollback=old-client-r8` documents a safe rehearsal.

## Resources

- PeopleGPT Guide

## Next Steps

Start with `juicebox-install-auth`.
