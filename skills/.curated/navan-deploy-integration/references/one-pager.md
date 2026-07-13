# navan-deploy-integration — One-Pager

Step-by-step deployment of Navan integrations with ERP, HRIS, and identity systems.

## The Problem

Connecting Navan to enterprise systems like NetSuite, Workday, or Okta requires navigating multiple integration methods (direct API, SCIM, SFTP, SSO) with inconsistent documentation. Teams waste weeks on trial-and-error, misconfigured field mappings, and broken user provisioning flows that leave employees unable to book travel.

## The Solution

This skill provides a structured deployment checklist for each integration type: ERP systems for expense sync (NetSuite, Sage Intacct, Xero), HRIS for user provisioning (Workday, BambooHR, ADP), and identity providers for SSO (Okta, Azure AD). Each checklist includes prerequisite configuration, API authentication setup, field mapping, testing procedures, and rollback steps.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | IT administrators, systems integrators, DevOps engineers deploying Navan in enterprise environments |
| **What** | Integration deployment checklists, OAuth credential configuration, field mapping templates, SCIM provisioning setup, SSO configuration |
| **When** | Initial Navan rollout, adding a new ERP connector, onboarding HRIS user sync, enabling SSO for the organization |

## Key Features

1. **ERP Expense Sync** — Deploy NetSuite, Sage Intacct, Xero, or QuickBooks connectors with correct GL code and cost center mappings
2. **HRIS User Provisioning** — Configure Workday, BambooHR, or ADP to auto-provision and deprovision Navan users via SCIM
3. **SSO Deployment** — Set up Okta or Azure AD SAML/OIDC with proper attribute mapping and JIT provisioning

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
