---
name: langchain-enterprise-rbac
description: |
  Implement enterprise role-based access control for LangChain applications.
  Use when implementing user permissions, multi-tenant access,
  or enterprise security controls for LLM applications.
  Trigger with phrases like "langchain RBAC", "langchain permissions",
  "langchain access control", "langchain multi-tenant", "langchain enterprise auth".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# LangChain Enterprise RBAC

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Implement role-based access control (RBAC) for LangChain applications with multi-tenant support, model access control, and usage quotas.

## Prerequisites
- LangChain application with user authentication
- Identity provider (Auth0, Okta, Azure AD)
- Understanding of RBAC concepts

## Instructions

### Step 1: Define Permission Model
Create `Permission` enum with chain, model, feature, and admin permissions. Define roles (viewer, user, power_user, admin) mapping to permission sets.

### Step 2: Implement User and Tenant Management
Create `Tenant` and `User` models with role-based permission resolution. Users belong to tenants with monthly token limits.

### Step 3: Enforce Permissions
Build `PermissionChecker` with FastAPI decorators (`@require_permission`) that validate user permissions before chain execution.

### Step 4: Control Model Access
Implement `ModelAccessController` that restricts LLM model access based on user permissions and tenant restrictions.

### Step 5: Isolate Tenants
Use context variables (`ContextVar`) for tenant isolation. Implement `TenantScopedVectorStore` that filters by tenant ID.

### Step 6: Manage Usage Quotas
Build `UsageQuotaManager` tracking per-tenant token usage with monthly resets and reporting.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete RBAC code.

## Output
- Permission model with roles
- User and tenant management
- Model access control
- Tenant isolation
- Usage quotas

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| 403 Forbidden | Insufficient permissions | Check user role assignment |
| Tenant data leak | Missing isolation | Verify ContextVar propagation |
| Quota exceeded | High usage | Upgrade tenant token limit |

## Examples


**Basic usage**: Apply langchain enterprise rbac to a standard project setup with default configuration options.

**Advanced scenario**: Customize langchain enterprise rbac for production environments with multiple constraints and team-specific requirements.

## Resources
- [RBAC Best Practices](https://auth0.com/docs/manage-users/access-control/rbac)
- [Multi-Tenant Architecture](https://docs.microsoft.com/en-us/azure/architecture/guide/multitenant/)
- [OAuth 2.0 Scopes](https://oauth.net/2/scope/)

## Next Steps
Use `langchain-data-handling` for data privacy controls.