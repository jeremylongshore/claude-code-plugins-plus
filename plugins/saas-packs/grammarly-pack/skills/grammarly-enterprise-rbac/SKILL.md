---
name: grammarly-enterprise-rbac
description: |
  Configure Grammarly enterprise role-based access control.
  Use when managing team access, configuring organization settings,
  or implementing Grammarly enterprise governance.
  Trigger with phrases like "grammarly enterprise", "grammarly teams",
  "grammarly rbac", "grammarly organization", "grammarly admin".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing, enterprise]
compatible-with: claude-code
---

# Grammarly Enterprise RBAC

## Overview

Manage Grammarly enterprise access with OAuth scopes and organization-level API credentials.

## OAuth Scopes

| Scope | Access |
|-------|--------|
| `scores-api:read` | Read writing scores |
| `scores-api:write` | Submit text for scoring |
| `ai-detection:read` | Read AI detection results |
| `plagiarism:read` | Read plagiarism results |

## Instructions

### Step 1: Separate Credentials Per Team

```typescript
const teamClients = {
  content: new GrammarlyClient(process.env.GRAMMARLY_CONTENT_ID!, process.env.GRAMMARLY_CONTENT_SECRET!),
  marketing: new GrammarlyClient(process.env.GRAMMARLY_MARKETING_ID!, process.env.GRAMMARLY_MARKETING_SECRET!),
};
```

### Step 2: Scope-Based Access

```typescript
function canUseAPI(team: string, api: 'score' | 'ai' | 'plagiarism'): boolean {
  const permissions: Record<string, string[]> = {
    content: ['score', 'ai', 'plagiarism'],
    marketing: ['score'],
    engineering: ['score', 'ai'],
  };
  return permissions[team]?.includes(api) ?? false;
}
```

## Resources

- [Grammarly Enterprise](https://www.grammarly.com/business)
