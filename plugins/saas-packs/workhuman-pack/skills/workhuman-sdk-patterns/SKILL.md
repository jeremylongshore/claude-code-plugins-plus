---
name: workhuman-sdk-patterns
description: |
  Workhuman sdk patterns for employee recognition and rewards API.
  Use when integrating Workhuman Social Recognition,
  or building recognition workflows with HRIS systems.
  Trigger: "workhuman sdk patterns".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hr, recognition, workhuman]
compatible-with: claude-code
---

# Workhuman Sdk Patterns

## Overview

Guidance for sdk patterns with Workhuman Social Recognition and rewards API.

## Instructions

### Key Workhuman API Concepts

- **Auth**: OAuth 2.0 client credentials flow
- **Recognition**: Peer-to-peer and manager nominations with points
- **Awards**: Configurable levels (bronze, silver, gold, platinum)
- **Values**: Company values attached to recognitions
- **HRIS Sync**: Bidirectional sync with Workday, SAP SuccessFactors
- **Integrations**: Microsoft Teams, Slack, Outlook native plugins

### Core API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/recognitions` | GET | List recognitions |
| `/api/v1/recognitions` | POST | Create nomination |
| `/api/v1/recognitions/:id` | GET | Get recognition status |
| `/api/v1/users` | GET | List employees |
| `/api/v1/rewards/catalog` | GET | Browse reward catalog |
| `/api/v1/rewards/redeem` | POST | Redeem points for reward |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Token expired | Re-authenticate |
| `403 Forbidden` | Insufficient permissions | Check role/permissions |
| `422 Validation` | Missing fields | Check required fields |
| `404 Not Found` | Invalid ID | Verify resource exists |

## Resources

- [Workhuman Platform](https://www.workhuman.com/)
- [Workhuman Integrations](https://www.workhuman.com/capabilities/integrations/)

## Next Steps

See related Workhuman skills for more patterns.
