# navan-security-basics — One-Pager

Secure Navan API credentials, configure SSO/SCIM, and align with Navan's compliance certifications.

## The Problem

Navan handles sensitive corporate travel and expense data under SOC 2 Type II, ISO 27001, and PCI DSS Level 1 compliance. However, integration developers often store OAuth client secrets in plaintext, skip token rotation, and neglect SSO configuration — creating security gaps that undermine the platform's built-in protections. Credential leaks in travel integrations expose corporate card data and employee PII.

## The Solution

This skill covers the full security surface for Navan integrations: OAuth 2.0 credential management with rotation schedules, environment-based secret storage, SSO/SAML configuration for supported identity providers (Okta, Azure AD, Google Workspace), and SCIM provisioning setup. It maps each practice to Navan's published compliance certifications.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | DevOps engineers, security teams, and backend developers managing Navan API integrations |
| **What** | Credential rotation automation, SSO/SAML configuration, SCIM user provisioning, secret storage patterns |
| **When** | Initial integration security hardening, compliance audits, onboarding a new identity provider, or after a credential exposure incident |

## Key Features

1. **OAuth 2.0 credential lifecycle** — Secure storage, rotation schedules, and revocation procedures for client_id/client_secret pairs
2. **SSO/SAML configuration** — Setup guides for Okta, Azure AD, AD FS, OneLogin, and Google Workspace identity providers
3. **SCIM provisioning** — Automated user lifecycle management through Okta or Entra ID directory sync

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
