# navan-ci-integration — One-Pager

Automates Navan API health checks, booking data validation, and compliance reporting inside CI/CD pipelines.

## The Problem

Teams integrating with Navan's REST API have no automated way to verify their integration remains healthy after code changes. A broken OAuth flow, changed endpoint response, or expired credential can ship to production undetected, causing expense sync failures or booking data corruption that finance teams discover days later.

## The Solution

This skill generates production-ready GitHub Actions workflows that authenticate against Navan's OAuth 2.0 endpoints, validate booking and expense data schemas, and produce compliance reports on every push or pull request. Secrets are managed through CI environment variables, and failures block deployment before reaching production.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | DevOps engineers, platform teams, developers maintaining Navan integrations |
| **What** | GitHub Actions workflow YAML, OAuth token management, API health check scripts, compliance report generation |
| **When** | Setting up CI for a new Navan integration, adding regression tests for expense sync, automating travel policy compliance checks |

## Key Features

1. **OAuth 2.0 CI Authentication** — Secure client_credentials flow using GitHub Actions secrets with automatic token refresh
2. **Booking Data Validation** — Schema checks against Navan API responses to catch breaking changes before deploy
3. **Compliance Reporting** — Automated travel policy adherence reports generated on every PR

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
