---
name: anthropic-enterprise-rbac
description: |
  Manage Anthropic workspaces, API keys, team access, and spending limits
  for enterprise Claude deployments.
  Trigger with "anthropic workspace", "anthropic team management",
  "claude enterprise", "anthropic api key management".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, anthropic, claude, enterprise, rbac]
---

# Anthropic Enterprise & Access Management

## Overview
Anthropic uses **Organizations** and **Workspaces** for access control. API keys are scoped to workspaces.

## Organization Structure
```
Organization (your-company)
├── Workspace: Production
│   ├── API Key: prod-backend (Tier 4)
│   └── API Key: prod-frontend-proxy (Tier 2)
├── Workspace: Staging
│   └── API Key: staging-all (Tier 2)
└── Workspace: Development
    └── API Key: dev-team (Tier 1)
```

## API Key Best Practices
| Practice | Why |
|----------|-----|
| One key per service/environment | Isolate blast radius |
| Name keys descriptively | `prod-recommendation-service` not `key-1` |
| Set spending limits per key | Prevent runaway costs from bugs |
| Rotate quarterly | Reduce exposure window |
| Never share dev and prod keys | Different rate limit tiers |

## Spending Limits
Set in Anthropic Console → Settings → Limits:
- **Monthly spend limit**: Hard cap on total spend
- **Per-key limits**: Not yet available — use separate workspaces

## Access Control Checklist
- [ ] Separate workspaces for dev/staging/prod
- [ ] Separate API keys per service
- [ ] Spending alerts configured
- [ ] Key rotation schedule (90 days)
- [ ] Offboarding process: revoke keys when team members leave
- [ ] Audit log review (Console → Logs)

## Output
- Successful operation confirmed
- Results logged to console

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| API Error | Check error type and status code | See `anthropic-common-errors` |

## Examples
See code blocks above for complete examples.

## Resources
- [Console Dashboard](https://console.anthropic.com)
- [Organization Settings](https://console.anthropic.com/settings)
- [Enterprise Plans](https://www.anthropic.com/enterprise)

## Next Steps
See `anthropic-migration-deep-dive` for migrating from other LLM providers.

## Prerequisites
- Completed `anthropic-enterprise-install-auth` setup
- Valid API credentials configured

## Instructions
Follow the steps in the sections above.
