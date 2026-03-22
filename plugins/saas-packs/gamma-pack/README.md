# Gamma Skill Pack

> Claude Code skill pack for Gamma.app integration — AI presentation generation (24 skills)

## Installation

```bash
/plugin install gamma-pack@claude-code-plugins-plus
```

## About Gamma

Gamma is an AI-powered content platform for creating presentations, documents, webpages, and social posts:

- **Generate API**: Create content from text prompts via REST API (v1.0 GA)
- **Output Formats**: Presentations, documents, webpages, social posts
- **Templates**: One-page template gammas for repeatable generation patterns
- **Export**: PDF, PPTX, PNG downloads via `exportAs` parameter
- **Themes**: Custom workspace themes applied to generated content
- **Credit System**: Image model tiers (Standard 2-15, Advanced 20-33, Premium 34-75, Ultra 30-125 credits)
- **No SDK**: Pure REST API with `X-API-KEY` header authentication
- **Async Pattern**: Generate -> poll -> retrieve (5s polling recommended)

## Skills Included

### Standard Skills (S01-S12)
| Skill | Description |
|-------|-------------|
| `gamma-install-auth` | API key setup, X-API-KEY header, verify with /themes, thin client wrapper |
| `gamma-hello-world` | Generate-poll-retrieve pattern in curl, TypeScript, and Python |
| `gamma-local-dev-loop` | Project structure, reusable client, mock server, integration tests |
| `gamma-sdk-patterns` | Typed client singleton, error class, poll helper, retry with backoff |
| `gamma-core-workflow-a` | Full parameter generation: themes, text modes, image options, batch |
| `gamma-core-workflow-b` | Template generation, export retrieval, sharing config, file downloads |
| `gamma-common-errors` | Auth errors, rate limits, generation failures, timeout handling |
| `gamma-debug-bundle` | curl diagnostic, TypeScript diagnose script, debug client, support template |
| `gamma-rate-limits` | Rate limit headers, exponential backoff, request queue, usage monitoring |
| `gamma-security-basics` | API key storage, rotation, webhook verification, audit logging |
| `gamma-prod-checklist` | 9-section checklist, circuit breaker, health check, verification script |
| `gamma-upgrade-migration` | v0.2 to v1.0 migration, breaking changes, rollback procedure |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `gamma-ci-integration` | GitHub Actions, vitest config, mock mode for PRs, integration tests |
| `gamma-deploy-integration` | Vercel, AWS Lambda, Cloud Run deployment with secret management |
| `gamma-webhooks-events` | Poll-based events, EventEmitter pattern, Bull queue, HTTP callbacks |
| `gamma-performance-tuning` | Smart polling, caching, parallel batch, keep-alive, text mode tuning |
| `gamma-cost-tuning` | Credit tracking, image tier optimization, template reuse, budget alerts |
| `gamma-reference-architecture` | Basic, service layer, and event-driven architecture patterns |

### Flagship Skills (F19-F24)
| Skill | Description |
|-------|-------------|
| `gamma-multi-env-setup` | Dev/staging/prod config, mock mode, secret manager, CI/CD environments |
| `gamma-observability` | Instrumented client, structured logging, Prometheus metrics, alerting |
| `gamma-incident-runbook` | Severity levels, 4 incident scenarios, diagnostic commands, communication |
| `gamma-data-handling` | Content sanitization, PII handling, GDPR requests, export archival |
| `gamma-enterprise-rbac` | App-level RBAC, permission matrix, multi-tenant, credit quotas |
| `gamma-migration-deep-dive` | PowerPoint/Slides content extraction, batch migration, template recreation |

## Usage

Skills trigger automatically when you discuss Gamma topics:

- "Help me set up Gamma API" triggers `gamma-install-auth`
- "Generate a presentation with Gamma" triggers `gamma-core-workflow-a`
- "Debug this Gamma error" triggers `gamma-common-errors`
- "Deploy my Gamma integration" triggers `gamma-deploy-integration`
- "Migrate from PowerPoint to Gamma" triggers `gamma-migration-deep-dive`

## Resources

- [Gamma Developer Docs](https://developers.gamma.app/)
- [Generate API Parameters](https://developers.gamma.app/guides/generate-api-parameters-explained)
- [Create from Template](https://developers.gamma.app/guides/create-from-template-api-parameters-explained)
- [API Changelog](https://developers.gamma.app/changelog)
- [Gamma Pricing](https://gamma.app/pricing)

## License

MIT
