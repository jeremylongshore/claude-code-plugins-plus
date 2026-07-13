# navan-migration-deep-dive — One-Pager

End-to-end migration guide for moving from SAP Concur or legacy TMC systems to Navan.

## The Problem

Migrating from SAP Concur or a legacy travel management company to Navan is a high-stakes project that touches every employee. Historical expense data must be preserved, travel policies must be recreated, user provisioning must be coordinated with HR, and there is no room for a gap in travel booking capability. Most organizations underestimate the parallel-running period and lack a structured cutover plan.

## The Solution

This skill provides a phased migration playbook covering data migration planning, user provisioning via SCIM or CSV, travel policy recreation in Navan's admin console, historical data export and archival, a parallel-running period with dual-system operation, and a detailed cutover checklist. It addresses SAP Concur-specific migration patterns including expense report mapping, approval workflow translation, and integration redirect.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Travel program managers, IT project leads, finance operations teams executing TMC migrations |
| **What** | Phased migration playbook with data mapping templates, user provisioning scripts, policy translation guide, and cutover checklist |
| **When** | SAP Concur contract renewal decision, TMC vendor switch, corporate travel program modernization, M&A system consolidation |

## Key Features

1. **SAP Concur Data Mapping** — Field-by-field mapping from Concur expense reports and itineraries to Navan's BOOKING and TRANSACTION tables
2. **Parallel Running Strategy** — Dual-system operation plan with traffic splitting, data reconciliation, and rollback triggers
3. **Cutover Checklist** — 30-point go/no-go checklist covering SSO switch, DNS redirect, policy activation, and user communications

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
