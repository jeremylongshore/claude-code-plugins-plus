# OneNote CI Integration — One-Pager

## The Problem

Testing OneNote integrations in CI requires Azure AD app registration, test tenant credentials stored as secrets, and mock strategies for Graph API responses. Without a structured approach, teams either skip CI entirely (shipping untested OneNote code) or leak credentials into logs and config files. The March 2025 app-only auth deprecation adds another layer: CI environments that relied on `ClientSecretCredential` must plan for the transition while keeping pipelines green.

## The Solution

Two-tier CI strategy: mock-only PR checks that need zero Azure credentials (using MSW to intercept Graph API calls) and nightly live integration tests with proper credential isolation. Includes complete GitHub Actions workflows, realistic test fixtures, test isolation via unique prefixes, and rate-limit-aware parallel execution.

## Who / What / When / Where / Why

| | |
|---|---|
| **Who** | Backend developers and DevOps engineers building OneNote integrations |
| **What** | GitHub Actions workflows with mock and live test strategies for Graph API |
| **When** | Setting up CI for a new OneNote project or migrating existing test suites |
| **Where** | GitHub Actions, Azure AD test tenants, local development environments |
| **Why** | OneNote API testing requires credential management, rate limit awareness, and mock strategies that most CI templates do not address |

## Key Differentiators

- Zero-credential mock strategy for PR checks — no Azure setup needed to start testing
- Realistic MSW handlers that simulate Graph API error responses (400, 429) not just happy paths
- Test isolation with unique prefixes and cleanup awareness (OneNote notebooks cannot be API-deleted)
- Rate limit guard that respects the 600 req/60s per-user limit across parallel test jobs

## Stack

| Component | Technology |
|-----------|-----------|
| API | Microsoft Graph v1.0 |
| Auth | MSAL (delegated); ClientSecretCredential for CI only (deprecated warning) |
| SDK (Python) | msgraph-sdk + azure-identity |
| SDK (Node) | @microsoft/microsoft-graph-client + @azure/identity |
| Mock Framework | MSW (Mock Service Worker) |
| CI Platform | GitHub Actions |
| Test Runner | Vitest |
