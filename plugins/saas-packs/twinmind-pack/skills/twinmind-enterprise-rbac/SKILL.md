---
name: twinmind-enterprise-rbac
description: |
  Implement enterprise role-based access control for TwinMind.
  Use when setting up team permissions, configuring SSO/SAML,
  or implementing organization-level access policies.
  Trigger with phrases like "twinmind RBAC", "twinmind permissions",
  "twinmind enterprise access", "twinmind SSO", "twinmind team management".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# TwinMind Enterprise RBAC

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Enterprise-grade role-based access control for TwinMind with SSO/SAML integration, team management, resource-level authorization, and access audit logging.

## Prerequisites
- TwinMind Enterprise account
- Admin access to TwinMind organization
- Identity provider (Okta, Azure AD, Google Workspace)
- Understanding of RBAC concepts

## Instructions

### Step 1: Define Roles and Permissions
Create `Permission` enum covering transcript, summary, action item, team, settings, billing, and admin permissions. Define role hierarchy: Viewer -> Member -> Manager -> Admin -> Owner with permission inheritance via `resolvePermissions()`.

### Step 2: Implement Permission Checking
Build `AuthorizationService` with `hasPermission()`, `hasAnyPermission()`, `hasAllPermissions()` methods. Support admin wildcard, explicit deny lists, and resource-level authorization (own transcripts vs all transcripts).

### Step 3: Configure SSO/SAML Integration
Set up SAML strategy with passport-saml. Map IdP attributes (email, name, groups) to TwinMind users. Configure group-to-role mapping (e.g., "TwinMind-Admins" -> admin role).

### Step 4: Team Management
Build `TeamManager` with create team, add/remove/invite members, role updates, and sync to TwinMind organization. Enforce permission checks on team operations.

### Step 5: Access Audit Logging
Create `AccessAuditLogger` that records all access attempts (granted and denied) with user, action, resource, IP, and user agent. Send to SIEM if configured. Add Express middleware for automatic audit trail.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete RBAC code including Permission enum, role definitions, SSO config, team management, and audit logging.

## Output
- Role and permission definitions
- Permission checking service
- SSO/SAML configuration
- Team management functionality
- Access audit logging

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| SSO login failed | Certificate mismatch | Update IdP certificate |
| Role not syncing | SCIM misconfigured | Check provisioning setup |
| Permission denied | Wrong role assigned | Review role mapping |
| Audit gaps | Middleware not applied | Add to all routes |

## Examples


**Basic usage**: Apply twinmind enterprise rbac to a standard project setup with default configuration options.

**Advanced scenario**: Customize twinmind enterprise rbac for production environments with multiple constraints and team-specific requirements.

## Resources
- [TwinMind Enterprise](https://twinmind.com/enterprise)
- [SAML 2.0 Specification](https://docs.oasis-open.org/security/saml/v2.0/)
- [SCIM Protocol](https://scim.cloud/)

## Next Steps
For migration from other tools, see `twinmind-migration-deep-dive`.