# navan-core-workflow-b — One-Pager

Manage expense reporting and transaction data through the Navan Expense API, including receipt handling, approval workflows, and ERP synchronization.

## The Problem

Navan Expense management requires a separate API enablement from Navan support, and the transaction data model differs significantly from the booking/travel side. Finance teams need programmatic access to expense transactions for reconciliation, audit, and ERP sync, but the Expense Transaction API is not self-service. Developers must understand the enablement process, the TRANSACTION table schema, and how to build approval and sync workflows around limited API surface.

## The Solution

This skill covers the end-to-end expense workflow: requesting Expense API enablement, querying transaction data, building approval chain integrations, and syncing expense records to ERP systems like NetSuite, Sage Intacct, Xero, and QuickBooks. It handles the TRANSACTION table's incremental data model and maps expense categories to GL codes.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Finance engineers and integration developers building expense pipelines |
| **What** | Expense transaction retrieval, approval workflow patterns, and ERP sync configurations |
| **When** | Setting up expense reporting automation, building approval bots, or integrating Navan expenses with accounting systems |

## Key Features

1. **Expense API enablement guide** — Step-by-step process to request and verify Expense Transaction API access
2. **ERP sync patterns** — Integration blueprints for NetSuite, Sage Intacct, Xero, and QuickBooks
3. **Approval workflow automation** — Programmatic expense routing based on amount thresholds and department policies

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
