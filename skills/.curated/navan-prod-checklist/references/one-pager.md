# navan-prod-checklist — One-Pager

Comprehensive production readiness checklist for Navan API integrations covering security, reliability, and compliance.

## The Problem

Launching a Navan integration into production without systematic verification leads to preventable outages. OAuth credentials stored in plaintext, missing rate limit handling, no alerting on API failures, unchecked SSO/SCIM sync, and no compliance audit trail are common gaps that surface only after incidents occur. Navan credentials are viewable only once, making credential management mistakes especially costly.

## The Solution

This skill provides a gated production readiness checklist organized into security, reliability, observability, and compliance domains. Each checkpoint includes verification commands or API calls to confirm readiness. The checklist covers OAuth credential rotation planning, error alerting configuration, rate limit handling, data backup strategy, SSO verification, SCIM sync validation, and compliance audit trails aligned with Navan's SOC 2 Type II and ISO 27001 certifications.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Integration engineers, security teams, DevOps leads preparing Navan integrations for production |
| **What** | Domain-organized checklist with verification commands for credentials, alerting, rate limits, SSO, SCIM, and compliance |
| **When** | Pre-launch gate review, quarterly security audits, post-incident hardening, compliance certification preparation |

## Key Features

1. **Credential Rotation Plan** — OAuth client_id/client_secret rotation procedure with zero-downtime swap strategy
2. **SSO and SCIM Validation** — Automated checks for SAML SSO login flow and SCIM user provisioning sync
3. **Compliance Audit Trail** — Logging configuration aligned with SOC 2 Type II, ISO 27001, and PCI DSS L1 requirements

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
