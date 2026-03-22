---
name: podium-local-dev-loop
description: |
  Podium local dev loop — business messaging and communication platform integration.
  Use when working with Podium API for messaging, reviews, or payments.
  Trigger with phrases like "podium local dev loop", "podium-local-dev-loop".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, podium, messaging, reviews, payments]
compatible-with: claude-code, codex, openclaw
---

# Podium Local Dev Loop

## Overview
Implementation patterns for Podium local dev loop using the REST API with OAuth2 authentication.

## Prerequisites
- Completed `podium-install-auth` setup
- Valid OAuth2 access token

## Instructions

### Step 1: API Call Pattern
```typescript
import axios from 'axios';

const podium = axios.create({
  baseURL: 'https://api.podium.com/v4',
  headers: { 'Authorization': `Bearer ${process.env.PODIUM_ACCESS_TOKEN}` },
});

const { data } = await podium.get('/locations');
console.log(`Locations: ${data.data.length}`);
```

## Output
- Podium API integration for local dev loop
- OAuth2 authenticated requests
- Error handling and retry logic

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Expired token | Refresh OAuth token |
| 429 Rate Limited | Too many requests | Implement backoff |
| 403 Forbidden | Missing scope | Update OAuth app scopes |

## Resources
- [Podium Developer Portal](https://developer.podium.com/)
- [Podium API Docs](https://docs.podium.com)

## Next Steps
See related Podium skills for more workflows.
