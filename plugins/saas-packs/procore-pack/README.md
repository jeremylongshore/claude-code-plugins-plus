# Procore Skill Pack

> Claude Code skill pack for Procore — construction management, projects, RFIs, submittals, and project management API (24 skills)

## What This Covers

Procore is a construction management platform. This pack covers the **Procore REST API** for managing projects, RFIs, submittals, daily logs, drawings, and construction workflows. Auth via OAuth2 (client credentials or authorization code).

**Key APIs:** Companies, Projects, RFIs, Submittals, Documents, Daily Logs, Photos, Observations. Base URL: `https://api.procore.com/rest/v1.0/`. Auth: OAuth2 Bearer token.

## Installation

```bash
/plugin install procore-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)
| Skill | Description |
|-------|-------------|
| `procore-install-auth` | OAuth2 setup (client credentials or authorization code flow) |
| `procore-hello-world` | List companies, get project, create an RFI |
| `procore-local-dev-loop` | Sandbox API testing, mock responses, pytest |
| `procore-sdk-patterns` | Python SDK wrapper, pagination, error handling |
| `procore-core-workflow-a` | RFI workflow: create, assign, respond, close |
| `procore-core-workflow-b` | Submittal workflow: create, review, approve/reject |
| `procore-common-errors` | Fix OAuth errors, 403/404, pagination issues |
| `procore-debug-bundle` | Collect API logs, project state, error traces |
| `procore-rate-limits` | Handle 429 errors with backoff |
| `procore-security-basics` | OAuth credential management, scope control |
| `procore-prod-checklist` | Production deployment checklist |
| `procore-upgrade-migration` | API version migration (v1.0 to v1.1) |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `procore-ci-integration` | CI pipeline with sandbox Procore API tests |
| `procore-deploy-integration` | Deploy construction integration service |
| `procore-webhooks-events` | Handle project, RFI, submittal change events |
| `procore-performance-tuning` | Batch operations, efficient project queries |
| `procore-cost-tuning` | Optimize API calls and data sync |
| `procore-reference-architecture` | Construction integration architecture |

### Flagship Skills (F19-F24)
| Skill | Description |
|-------|-------------|
| `procore-multi-env-setup` | Sandbox/production environment configuration |
| `procore-observability` | Monitoring Procore API health and latency |
| `procore-incident-runbook` | Triage Procore integration failures |
| `procore-data-handling` | Construction document and photo management |
| `procore-enterprise-rbac` | Project-level permissions and role management |
| `procore-migration-deep-dive` | Migrate construction data to/from Procore |

## Key Documentation

- [Procore Developers](https://developers.procore.com/)
- [REST API Reference](https://developers.procore.com/reference/rest)
- [OAuth2 Endpoints](https://developers.procore.com/documentation/oauth-endpoints)
- [Python SDK](https://github.com/fylein/procore-sdk-py)

## License

MIT
