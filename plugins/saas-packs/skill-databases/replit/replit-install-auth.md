# replit-install-auth

## Skill Scaffold

```
replit-install-auth/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Install and configure Replit CLI authentication including API token setup, OAuth flow, and connection verification.
**Workflow:** First skill in the onboarding sequence - establishes CLI access and authentication before any programmatic Replit operations.
**Relates to:** Prerequisite for replit-hello-world and all other skills; integrates with replit-secrets-management for credential storage.

## Summary

This skill handles the initial setup of Replit CLI and API authentication. It guides developers through installing the Replit CLI via npm, configuring API tokens through OAuth or manual token generation, setting up environment variables for secure token storage, and verifying the connection to Replit workspaces. This is the essential first step for any programmatic interaction with Replit outside the browser IDE.
