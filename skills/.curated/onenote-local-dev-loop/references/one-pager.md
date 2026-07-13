# OneNote Local Dev Loop — One-Pager

## The Problem

Testing OneNote integrations requires Azure AD credentials and live Graph API calls. Every dev session starts with authentication friction (device code flow, token expiry), and rapid iteration risks hitting the 600 req/60s rate limit. Developers without Azure credentials cannot contribute to OneNote integration code at all. There is no official OneNote sandbox or emulator.

## The Solution

A local development loop using MSW (TypeScript) or responses (Python) to intercept Graph API calls and return realistic fixture data. Supports environment variable switching between mock and live modes, includes XHTML output format fixtures, and provides a capture script to refresh fixtures from the live API. Tests run instantly without Azure credentials.

## Who / What / When / Where / Why

| | |
|---|---|
| **Who** | Developers building or contributing to OneNote integrations, CI/CD pipelines |
| **What** | Mock Graph API server, fixture data, environment switching, test isolation patterns |
| **When** | During development and CI — switch to live mode only for integration tests |
| **Where** | Local development environment, CI pipeline test stage |
| **Why** | No official OneNote sandbox exists; live API requires credentials and has rate limits |

## Key Differentiators

- MSW intercepts at network level — production code needs zero changes
- Fixtures include output HTML format (which differs from input format)
- Simulates error conditions: 429 rate limits, silent upload failures, 403 auth errors
- Fixture capture script refreshes mocks from real Graph API responses

## Stack

| Component | Technology |
|-----------|-----------|
| API | Microsoft Graph v1.0 (mocked) |
| Auth | Bypassed in mock mode, MSAL delegated in live mode |
| Mock (Node) | MSW (Mock Service Worker) |
| Mock (Python) | responses library |
| Test (Node) | vitest |
| Test (Python) | pytest |
