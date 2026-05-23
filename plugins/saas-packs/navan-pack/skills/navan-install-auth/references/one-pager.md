# navan-install-auth — One-Pager

Set up OAuth 2.0 authentication for the Navan REST API using client credentials.

## The Problem

Navan has no public SDK — all API access requires raw REST calls with OAuth 2.0 bearer tokens. Developers waste time figuring out the credential creation flow (Admin > Travel admin > Settings > Integrations > Navan API Credentials) and building token exchange logic from scratch. Credentials are only viewable once, so mishandling them means regenerating.

## The Solution

This skill walks through the complete OAuth 2.0 setup: creating API credentials in the Navan admin dashboard, securely storing client_id and client_secret, implementing the token exchange in both TypeScript and Python, and verifying the connection with a real API call.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Backend developers integrating Navan travel/expense data into internal tools |
| **What** | Working OAuth 2.0 auth flow with .env setup, token exchange code, and connection verification |
| **When** | Starting a new Navan integration, rotating credentials, or onboarding a teammate to the API |

## Key Features

1. **Dashboard walkthrough** — Step-by-step credential creation in the Navan admin console
2. **Dual-language auth code** — Token exchange implementations in TypeScript (fetch) and Python (requests)
3. **Secure credential storage** — .env-based secrets management with .gitignore enforcement

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
