# Ramp Skill Pack

> Claude Code skill pack for Ramp — corporate card management, expense tracking, accounting integration, and spend management API (24 skills)

## What This Covers

Ramp is a corporate card and spend management platform. This pack covers the **Ramp Developer API** for issuing virtual/physical cards, managing transactions, syncing accounting data, and controlling spend policies.

**Key APIs:** Cards, Transactions, Users, Departments, Vendors, Accounting Sync, Reimbursements, Receipts. Base URL: `https://api.ramp.com/v1/` (prod) or `https://sandbox-api.ramp.com/v1/` (sandbox). Auth: OAuth2 client credentials.

## Installation

```bash
/plugin install ramp-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)
| Skill | Description |
|-------|-------------|
| `ramp-install-auth` | OAuth2 client credentials, sandbox vs production setup |
| `ramp-hello-world` | List cards, get transaction, check user |
| `ramp-local-dev-loop` | Sandbox API testing, mock transactions |
| `ramp-sdk-patterns` | API client wrapper, token refresh, pagination |
| `ramp-core-workflow-a` | Card management: issue virtual cards, set limits, suspend |
| `ramp-core-workflow-b` | Transaction and expense workflow: list, categorize, sync |
| `ramp-common-errors` | Fix OAuth errors, card issuance failures, sync issues |
| `ramp-debug-bundle` | Collect API logs, card state, transaction records |
| `ramp-rate-limits` | Handle API rate limits with backoff |
| `ramp-security-basics` | OAuth credential management, card data handling |
| `ramp-prod-checklist` | Production deployment checklist |
| `ramp-upgrade-migration` | API version migration |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `ramp-ci-integration` | CI pipeline with sandbox Ramp API tests |
| `ramp-deploy-integration` | Deploy expense management integration |
| `ramp-webhooks-events` | Handle transaction, card, and receipt events |
| `ramp-performance-tuning` | Batch transaction queries, efficient sync |
| `ramp-cost-tuning` | Optimize API usage and sync frequency |
| `ramp-reference-architecture` | Expense management integration architecture |

### Flagship Skills (F19-F24)
| Skill | Description |
|-------|-------------|
| `ramp-multi-env-setup` | Sandbox/production environment configuration |
| `ramp-observability` | Monitor Ramp API health and sync status |
| `ramp-incident-runbook` | Triage card and transaction sync failures |
| `ramp-data-handling` | PCI compliance, transaction data handling |
| `ramp-enterprise-rbac` | Department-level card controls and approvals |
| `ramp-migration-deep-dive` | Migrate from legacy expense systems to Ramp |

## Key Documentation

- [Ramp API Documentation](https://docs.ramp.com/)
- [Authorization](https://docs.ramp.com/developer-api/v1/authorization)
- [Cards and Funds](https://docs.ramp.com/developer-api/v1/cards-and-funds)
- [Accounting Guide](https://docs.ramp.com/developer-api/v1/guides/accounting)

## License

MIT
