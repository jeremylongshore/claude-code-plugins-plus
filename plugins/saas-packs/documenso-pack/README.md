# Documenso Skill Pack

> Claude Code skill pack for Documenso integration — open-source document signing (24 skills)

## Installation

```bash
/plugin install documenso-pack@claude-code-plugins-plus
```

## About Documenso

Documenso is the open-source DocuSign alternative, providing:

- **Document Signing**: Electronic signatures with full legal compliance
- **Templates**: Reusable document templates with pre-configured fields
- **API v2**: Modern REST API with TypeScript, Python, and Go SDKs
- **Webhooks**: Real-time event notifications (document.completed, document.signed, etc.)
- **Self-Hosting**: Full control with Docker deployment, AGPL-licensed
- **Embedding**: React, Vue, Svelte components for embedded signing flows
- **Teams**: Multi-user collaboration with shared documents and templates
- **Enterprise**: SSO (OIDC), audit logging, and compliance features

## Skills Included

### Standard Skills (S01-S12)
| Skill | Description |
|-------|-------------|
| `documenso-install-auth` | Configure SDK, generate API keys, verify connection (TS + Python) |
| `documenso-hello-world` | Create, upload, add recipient, add field, send — in one script |
| `documenso-local-dev-loop` | Project structure, Docker self-hosted, mock client, cleanup scripts |
| `documenso-sdk-patterns` | Singleton client, typed services, error handling, retry, mocks |
| `documenso-core-workflow-a` | Document creation, recipient roles, signing order, field positioning |
| `documenso-core-workflow-b` | Templates, direct signing links, embedded React, v2 envelopes |
| `documenso-common-errors` | HTTP error reference, field validation, webhook troubleshooting |
| `documenso-debug-bundle` | Connectivity test, diagnostic script, debug logging, support tickets |
| `documenso-rate-limits` | Fair-use model, exponential backoff, request queue, circuit breaker |
| `documenso-security-basics` | API key management, rotation, webhook verification, signing certs |
| `documenso-prod-checklist` | 30+ item go-live checklist, verification script, rollback procedure |
| `documenso-upgrade-migration` | v1 to v2 API migration, SDK upgrades, self-hosted container upgrades |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `documenso-ci-integration` | GitHub Actions, unit tests with mocks, integration tests against staging |
| `documenso-deploy-integration` | Docker, self-hosted Docker Compose, AWS Lambda, Cloud Run |
| `documenso-webhooks-events` | 7 event types, Express handler, verification, idempotent processing |
| `documenso-performance-tuning` | Templates reduce 5 calls to 2, caching, batch with p-queue, async jobs |
| `documenso-cost-tuning` | Pricing comparison, template reuse, self-hosting cost analysis |
| `documenso-reference-architecture` | Project layout, layered services, data flow diagrams, setup script |

### Flagship Skills (F19-F24)
| Skill | Description |
|-------|-------------|
| `documenso-multi-env-setup` | Dev/staging/prod configs, client factory, mock client, env guards |
| `documenso-observability` | Instrumented client, structured logging, health checks, Prometheus |
| `documenso-incident-runbook` | Severity levels, diagnostic commands, 4 incident scenarios, circuit breaker |
| `documenso-data-handling` | Download signed PDFs, PII sanitization, GDPR requests, S3 archival |
| `documenso-enterprise-rbac` | Team API keys, app-level RBAC, SSO config, multi-tenant architecture |
| `documenso-migration-deep-dive` | DocuSign/HelloSign migration, Strangler Fig pattern, template recreation |

## Usage

Skills trigger automatically when you discuss Documenso topics:

- "Help me set up Documenso" triggers `documenso-install-auth`
- "Debug this Documenso error" triggers `documenso-common-errors`
- "Configure Documenso webhooks" triggers `documenso-webhooks-events`
- "Deploy my Documenso integration" triggers `documenso-deploy-integration`
- "Migrate from DocuSign" triggers `documenso-migration-deep-dive`

## Resources

- [Documenso Documentation](https://docs.documenso.com)
- [Documenso API v2](https://openapi.documenso.com)
- [TypeScript SDK](https://github.com/documenso/sdk-typescript)
- [Python SDK](https://github.com/documenso/sdk-python)
- [Documenso GitHub](https://github.com/documenso/documenso)
- [Self-Hosting Guide](https://docs.documenso.com/developers/self-hosting)

## License

MIT
