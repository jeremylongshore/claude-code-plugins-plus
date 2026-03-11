---
name: deepgram-enterprise-rbac
description: |
  Configure enterprise role-based access control for Deepgram integrations.
  Use when implementing team permissions, managing API key scopes,
  or setting up organization-level access controls.
  Trigger with phrases like "deepgram RBAC", "deepgram permissions",
  "deepgram access control", "deepgram team roles", "deepgram enterprise".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Deepgram Enterprise RBAC

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Implement role-based access control for enterprise Deepgram deployments with five roles (Admin, Developer, Analyst, Service, Auditor), scoped API keys, team management, permission middleware, and automated key rotation.

## Prerequisites
- Deepgram enterprise account
- Multiple projects configured
- Team management system
- Audit logging enabled

## Instructions

### Step 1: Define Roles and Permissions
Create five roles with mapped Deepgram scopes: Admin (manage:*, listen:*, usage:*, keys:*), Developer (listen:*, usage:read), Analyst (usage:read), Service (listen:*), Auditor (usage:read, keys:read).

### Step 2: Build RBAC Service
Implement user API key creation with role-based scopes. Keys are scoped to team projects with expiration dates (90 days for service accounts, 365 for users). Store key references, not keys themselves.

### Step 3: Implement Permission Middleware
Create Express middleware that checks user permissions before route handlers. Return 401 for unauthenticated, 403 for unauthorized requests.

### Step 4: Set Up Team Management
Create teams linked to Deepgram projects. Add/remove members with role assignment. Auto-provision/revoke API keys on membership changes.

### Step 5: Enable API Key Rotation
Scan for keys expiring within 7 days. Revoke old key, create new key with same scopes, notify user. Run as scheduled job.

### Step 6: Configure Audit Logging
Log all key creation, revocation, role changes, and permission denials with timestamps and actor IDs.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Five-role permission system with Deepgram scope mapping
- Scoped API key lifecycle management
- Express permission middleware
- Team-based access control
- Automated key rotation
- RBAC audit trail

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Permission denied | Wrong role | Request role upgrade from admin |
| Key expired | No rotation | Enable auto-rotation job |
| Team not found | Deleted team | Verify team exists before operations |
| Scope mismatch | Role change | Revoke and recreate key on role update |

## Examples

### Permission Scopes
| Scope | Description | Roles |
|-------|-------------|-------|
| `listen:*` | All transcription | Admin, Developer, Service |
| `manage:*` | All management | Admin |
| `usage:read` | View usage | Admin, Developer, Analyst, Auditor |
| `keys:read` | View API keys | Admin, Auditor |
| `keys:write` | Create/delete keys | Admin |

### Access Control Matrix
| Action | Admin | Developer | Analyst | Service | Auditor |
|--------|-------|-----------|---------|---------|---------|
| Transcribe | Yes | Yes | No | Yes | No |
| View usage | Yes | Yes | Yes | No | Yes |
| Manage keys | Yes | No | No | No | No |
| View audit | Yes | No | No | No | Yes |

## Resources
- [Deepgram API Key Management](https://developers.deepgram.com/docs/api-key-management)
- [Project Management](https://developers.deepgram.com/docs/projects)
- [Enterprise Features](https://deepgram.com/enterprise)
