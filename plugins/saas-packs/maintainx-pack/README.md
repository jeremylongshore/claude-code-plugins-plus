# MaintainX Skill Pack

> Claude Code skill pack for MaintainX CMMS integration (24 skills)

## Installation

```bash
/plugin install maintainx-pack@claude-code-plugins-plus
```

## About MaintainX

[MaintainX](https://getmaintainx.com) is a cloud-based Computerized Maintenance Management System (CMMS) used by industrial teams to manage maintenance operations. The REST API at `api.getmaintainx.com/v1` provides programmatic access to work orders, assets, locations, procedures, meters, parts inventory, and team management.

**Key facts:**
- REST API v1 at `https://api.getmaintainx.com/v1/`
- Bearer token authentication (API key from Settings > Integrations)
- Cursor-based pagination with `cursor` and `limit` parameters
- Professional or Enterprise plan required for API access
- Official documentation at [maintainx.dev](https://maintainx.dev/)

## Skills Included

### Standard Skills (S01-S12)
| Skill | Description |
|-------|-------------|
| `maintainx-install-auth` | REST API client setup with TypeScript and Python wrappers |
| `maintainx-hello-world` | Create first work order via API and curl |
| `maintainx-local-dev-loop` | Development environment with sandbox testing |
| `maintainx-sdk-patterns` | REST patterns, cursor pagination, typed interfaces |
| `maintainx-core-workflow-a` | Work order lifecycle (OPEN > IN_PROGRESS > COMPLETED) |
| `maintainx-core-workflow-b` | Asset and location management |
| `maintainx-common-errors` | HTTP error codes, validation errors, auth issues |
| `maintainx-debug-bundle` | API diagnostics, request tracing, response inspection |
| `maintainx-rate-limits` | Rate limiting, cursor pagination, request optimization |
| `maintainx-security-basics` | API key security, org isolation, access control |
| `maintainx-prod-checklist` | Production deployment and integration checklist |
| `maintainx-upgrade-migration` | API version migration and breaking changes |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `maintainx-ci-integration` | CI/CD pipeline with API testing |
| `maintainx-deploy-integration` | Deployment automation and infrastructure |
| `maintainx-webhooks-events` | Webhook setup and event handling |
| `maintainx-performance-tuning` | API performance, caching, batch operations |
| `maintainx-cost-tuning` | API usage optimization and cost management |
| `maintainx-reference-architecture` | Production architecture with sync patterns |

### Flagship Skills (F19-F24)
| Skill | Description |
|-------|-------------|
| `maintainx-multi-env-setup` | Dev/staging/prod with org-level isolation |
| `maintainx-observability` | API monitoring, alerting, and dashboards |
| `maintainx-incident-runbook` | API failure triage and recovery |
| `maintainx-data-handling` | Data sync, ETL patterns, export workflows |
| `maintainx-enterprise-rbac` | Multi-org access, role-based permissions |
| `maintainx-migration-deep-dive` | Platform migration from other CMMS systems |

## Quick Start

```bash
# Set API key
export MAINTAINX_API_KEY="your-api-key"

# Create a work order
curl -X POST https://api.getmaintainx.com/v1/workorders \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title": "HVAC Filter Replacement", "priority": "MEDIUM", "status": "OPEN"}'

# List open work orders
curl -s "https://api.getmaintainx.com/v1/workorders?status=OPEN&limit=5" \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" | jq '.workOrders[] | {id, title, status}'
```

## API Reference

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/workorders` | GET, POST | Work order CRUD |
| `/workorders/{id}` | GET, PATCH, DELETE | Single work order |
| `/assets` | GET, POST | Equipment and asset management |
| `/locations` | GET, POST | Facility and area management |
| `/users` | GET | Team member listing |
| `/teams` | GET | Team management |
| `/meters` | GET, POST | Meter readings |
| `/parts` | GET, POST | Parts and inventory |
| `/procedures` | GET | Standard operating procedures |

## Resources

- [MaintainX API Documentation](https://maintainx.dev/)
- [MaintainX Help Center](https://help.getmaintainx.com/)
- [API Key Generation](https://intercom.help/maintainx/en/articles/5658848)
- [Work Orders Guide](https://help.getmaintainx.com/about-work-orders)

## License

MIT
