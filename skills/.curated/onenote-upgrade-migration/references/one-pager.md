# OneNote Upgrade & Migration — One-Pager

## The Problem

Microsoft shipped three breaking changes to OneNote integrations in under two years: webhook decommissioning (June 2023), search endpoint deprecation (April 2024), and app-only auth deprecation (March 2025). The Graph SDK itself had a major version bump (v5 to v6) that changed client initialization from callback-based to middleware-based. Teams discover these changes when their production code starts returning 403s and 404s with no clear migration path — and each change requires different code modifications, Azure portal updates, and verification steps.

## The Solution

Exact before/after code diffs for each breaking change with verification steps and rollback strategies. Covers auth migration (ClientSecretCredential to DeviceCodeCredential), webhook replacement (subscriptions to delta polling), search endpoint migration (server-side to OData + client-side), and SDK v5 to v6 upgrade. Includes migration checklists and runtime feature detection.

## Who / What / When / Where / Why

| | |
|---|---|
| **Who** | Developers maintaining OneNote integrations that hit deprecation errors |
| **What** | Step-by-step migration guides with code diffs, checklists, and rollback strategies |
| **When** | After receiving 403/404 errors from previously working code, or proactively before deprecation dates |
| **Where** | TypeScript and Python OneNote integrations, Azure AD app registrations |
| **Why** | Three major breaking changes in two years with no unified migration guide; each requires different code, config, and portal changes |

## Key Differentiators

- Exact before/after diffs — not "update your code" but the actual lines to change
- Feature detection module for runtime compatibility checks (is search endpoint available, does this need delegated auth)
- Feature flag pattern for gradual auth migration without downtime
- Migration checklists with specific verification commands to run before merging

## Stack

| Component | Technology |
|-----------|-----------|
| API | Microsoft Graph v1.0 |
| Auth | MSAL (delegated — DeviceCodeCredential / InteractiveBrowserCredential) |
| SDK (Python) | msgraph-sdk + azure-identity |
| SDK (Node) | @microsoft/microsoft-graph-client@6.x + @azure/identity |
| Change Detection | Delta queries (replaces decommissioned webhooks) |
| Search | OData $filter + client-side content search (replaces deprecated search endpoint) |
