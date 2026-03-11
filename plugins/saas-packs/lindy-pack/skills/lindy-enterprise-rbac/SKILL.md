---
name: lindy-enterprise-rbac
description: |
  Configure enterprise role-based access control for Lindy AI.
  Use when setting up team permissions, managing access,
  or implementing enterprise security policies.
  Trigger with phrases like "lindy permissions", "lindy RBAC",
  "lindy access control", "lindy enterprise security".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lindy Enterprise RBAC

## Overview
Manage team-level access control for Lindy AI agents and automations. Lindy organizes access around workspaces where agents live, with team members assigned Owner, Editor, or Viewer roles that govern who can create, modify, run, or merely observe AI agents and their execution history.

## Prerequisites
- Lindy Team or Enterprise plan (per-agent pricing applies)
- Workspace owner or admin privileges
- Team members invited to the Lindy workspace

## Instructions

### Step 1: Map Organizational Roles to Lindy Permissions

### Step 2: Configure Team Membership via API

### Step 3: Restrict Agent Visibility per Team

### Step 4: Audit Agent Access

### Step 5: Enforce API Key Scoping
Create separate API keys per integration rather than sharing a single workspace key. Rotate keys on a 90-day schedule and revoke immediately when a team member leaves.


For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `403 Forbidden` on agent create | User has Viewer role | Promote to Editor in workspace settings |
| Agent not visible to teammate | Agent in private folder | Move to shared team folder or adjust visibility |
| API key returns `401` | Key revoked or expired | Generate new key in workspace settings |
| Cannot delete workspace | Not the Owner | Transfer ownership first via account settings |

## Examples


**Basic usage**: Apply lindy enterprise rbac to a standard project setup with default configuration options.

**Advanced scenario**: Customize lindy enterprise rbac for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [security implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Resources

- Official security documentation
- Community best practices and patterns
- Related skills in this plugin pack