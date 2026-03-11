---
name: langfuse-enterprise-rbac
description: |
  Configure Langfuse enterprise organization management and access control.
  Use when implementing team access controls, configuring organization settings,
  or setting up role-based permissions for Langfuse projects.
  Trigger with phrases like "langfuse RBAC", "langfuse teams",
  "langfuse organization", "langfuse access control", "langfuse permissions".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Langfuse Enterprise RBAC

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Configure enterprise-grade access control for Langfuse with role definitions, scoped API keys, project-based access, SSO integration, and RBAC audit logging.

## Prerequisites
- Langfuse organization/team account
- Understanding of role-based access patterns
- SSO provider (optional, for enterprise SSO)

## Instructions

### Step 1: Implement Role-Based Permissions
Define five roles (Owner, Admin, Member, Viewer, API Only) with granular permission maps for dashboard, traces, settings, members, billing, and data deletion.

### Step 2: Create Scoped API Keys
Generate API keys with specific permission scopes, project restrictions, IP allowlists, and custom rate limits.

### Step 3: Implement Project-Based Access
Build a project access controller that maps users to roles per project, with privilege escalation prevention.

### Step 4: Integrate SSO
Map IdP groups to Langfuse roles via SAML assertions. Enforce email domain validation.

### Step 5: Enable RBAC Audit Logging
Log all member additions, removals, role changes, and permission denials. Alert security team on denied access.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Role-based permission system (5 roles)
- Scoped API key management
- Project-level access control
- SSO group-to-role mapping
- RBAC audit trail

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Permission denied | Insufficient role | Request role upgrade from admin |
| SSO login fails | Wrong group mapping | Update group mapping config |
| API key rejected | Expired or scoped | Create new key with correct scope |
| Project not found | No access | Request project access from owner |

## Examples

### Access Control Matrix
| Action | Owner | Admin | Member | Viewer | API Only |
|--------|-------|-------|--------|--------|----------|
| View traces | Yes | Yes | Yes | Yes | No |
| Create traces | Yes | Yes | Yes | No | Yes |
| Delete traces | Yes | Yes | No | No | No |
| Manage members | Yes | Yes | No | No | No |
| Manage billing | Yes | No | No | No | No |

## Resources
- [Langfuse Organizations](https://langfuse.com/docs/teams)
- [Langfuse API Keys](https://langfuse.com/docs/api-reference)
- [SAML 2.0 Specification](https://wiki.oasis-open.org/security/FrontPage)