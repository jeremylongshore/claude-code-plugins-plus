# navan-entity-management — One-Pager

Manage users, departments, cost centers, and approval chains in Navan through the REST API and SCIM provisioning.

## The Problem

Enterprise Navan deployments require ongoing user lifecycle management: onboarding employees with correct travel policies, assigning cost centers and departments, configuring approval chains, and deprovisioning departed staff. Doing this manually in the admin console does not scale, and the relationship between Navan user management, SCIM provisioning (Okta/Entra ID), and travel policy assignment is poorly documented.

## The Solution

This skill provides entity management patterns using the GET /get_users endpoint for user retrieval, SCIM 2.0 provisioning for automated user lifecycle with identity providers, and admin console configuration for departments, cost centers, and approval hierarchies. It covers both API-driven and IdP-driven approaches for organizations of different sizes.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | IT admins and platform engineers managing Navan at scale (100+ employees) |
| **What** | User provisioning, department/cost center setup, approval chain configuration, and SCIM integration |
| **When** | Onboarding new departments, integrating with Okta/Entra ID, restructuring approval hierarchies, or auditing user access |

## Key Features

1. **User retrieval and audit** — Query all users via GET /get_users with filtering and role inspection
2. **SCIM provisioning** — Automated user lifecycle with Okta, Entra ID, and OneLogin
3. **Policy and approval chains** — Map departments to travel policies and configure multi-level approval routing

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
