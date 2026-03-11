---
name: windsurf-enterprise-rbac
description: |
  Configure Windsurf enterprise SSO, role-based access control, and organization management.
  Use when implementing SSO integration, configuring role-based permissions,
  or setting up organization-level controls for Windsurf.
  Trigger with phrases like "windsurf SSO", "windsurf RBAC",
  "windsurf enterprise", "windsurf roles", "windsurf permissions", "windsurf SAML".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Windsurf Enterprise RBAC

## Overview
Manage team access to Windsurf AI IDE features, workspace settings, and code generation capabilities. Windsurf (by Codeium) uses per-seat licensing with workspace roles that control access to AI features like Cascade (agentic flows), Supercomplete, and Command.

## Prerequisites
- Windsurf Pro or Enterprise plan (per-seat pricing)
- Organization admin access at windsurf.com/dashboard
- Identity provider for SSO (Enterprise only)

## Instructions

### Step 1: Configure Organization-Wide AI Policies
In Windsurf Admin Dashboard > Policies:
```yaml
# Recommended enterprise AI policy settings
ai_policies:
  code_context_sharing: "workspace_only"     # AI cannot see code outside workspace
  telemetry: "anonymized"                     # No raw code sent to telemetry
  allowed_models: ["windsurf-cascade", "windsurf-supercomplete"]
  code_generation_review: "suggest_only"      # AI suggests, human applies
  max_cascade_steps: 10                       # Limit agentic flow depth
```

### Step 2: Manage Seat Assignments
```yaml
# seat-allocation.yaml
teams:
  engineering:
    plan: pro
    seats: 25
    features: [cascade, supercomplete, command, inline_chat]
  design:
    plan: pro
    seats: 5
    features: [supercomplete, command]  # No cascade (agentic flows)
  contractors:
    plan: basic
    seats: 10
    features: [supercomplete]  # Limited AI features
```
Assign seats via Admin Dashboard > Members > Invite with Role.

### Step 3: Enable SSO (Enterprise Only)
In Admin Dashboard > Security > SSO:
- Configure SAML 2.0 with your IdP
- Map IdP groups to Windsurf workspace roles (Admin, Member)
- Enable "Enforce SSO" to block password login
- Set auto-provisioning for new users from approved email domains

### Step 4: Set Workspace Access Boundaries
Control which repositories and folders Windsurf AI can access:
```json
// .windsurf/settings.json (workspace-level)
{
  "ai.contextExclusions": [
    "**/secrets/**",
    "**/.env*",
    "**/credentials/**"
  ],
  "ai.allowedWorkspaces": ["src", "lib", "tests"]
}
```

### Step 5: Review AI Usage Metrics
Monitor the Admin Dashboard for per-user AI usage: completions accepted, Cascade flows run, and tokens consumed. Use this data for seat optimization (remove seats from users with <10 AI interactions per month).

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| AI features grayed out | Seat not assigned | Assign Pro seat in admin dashboard |
| Cascade flow blocked | `max_cascade_steps` exceeded | Increase limit or break task into smaller flows |
| SSO login fails | SAML certificate expired | Update certificate in IdP and Windsurf config |
| Code context leak concern | No exclusion rules set | Add `.windsurf/settings.json` with exclusions |

## Examples

**Basic usage**: Apply windsurf enterprise rbac to a standard project setup with default configuration options.

**Advanced scenario**: Customize windsurf enterprise rbac for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Resources

- Official Windsurf Enterprise Rbac documentation
- Community best practices and patterns
- Related skills in this plugin pack