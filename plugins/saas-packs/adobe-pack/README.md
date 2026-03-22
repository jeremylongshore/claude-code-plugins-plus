# Adobe Skill Pack

> 30 production-grade skills for Adobe Firefly Services, PDF Services, Photoshop API, Lightroom API, and I/O Events. Real OAuth Server-to-Server auth, real endpoints, real SDK patterns.

## What This Covers

| Adobe API | Skills | Key Operations |
|-----------|--------|----------------|
| **Firefly Services** | Core Workflow A, Hello World, Performance | Text-to-image, generative fill, expand image (v3 API) |
| **PDF Services** | Core Workflow B, Hello World, Cost Tuning | Create, extract, merge, document generation, PDF-to-Markdown |
| **Photoshop API** | Hello World, Migration, Known Pitfalls | Remove background (v2), smart objects, action playback |
| **Lightroom API** | SDK Patterns, Architecture Variants | Auto tone, presets, batch editing |
| **I/O Events** | Webhooks & Events, Security Basics | RSA-SHA256 signature verification, event registration |
| **Admin Console / UMAPI** | Enterprise RBAC | SCIM provisioning, product profiles, Federated ID |
| **App Builder** | Deploy Integration, Architecture Variants | Runtime actions, `aio` CLI, serverless deployment |

## Installation

```bash
/plugin install adobe-pack@claude-code-plugins-plus
```

## Skills (30)

### Standard (S01-S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `adobe-install-auth` | OAuth Server-to-Server setup via `ims-na1.adobelogin.com/ims/token/v3` |
| S02 | `adobe-hello-world` | Three working examples: Firefly generate, PDF extract, Photoshop cutout |
| S03 | `adobe-local-dev-loop` | `aio app run` + vitest mocking + integration tests |
| S04 | `adobe-sdk-patterns` | Singleton auth, typed API wrapper, retry, job polling, Zod validation |
| S05 | `adobe-core-workflow-a` | Firefly v3: text-to-image, generative fill, expand image (sync + async) |
| S06 | `adobe-core-workflow-b` | PDF Services: create from HTML, extract with Sensei AI, document generation |
| S07 | `adobe-common-errors` | 8 real errors: `invalid_token`, `403003`, `429`, content policy, `DISQUALIFIED` |
| S08 | `adobe-debug-bundle` | Diagnostic script: SDK versions, IMS token test, endpoint connectivity |
| S09 | `adobe-rate-limits` | Per-API rate tables, `Retry-After` aware backoff, p-queue batching |
| S10 | `adobe-security-basics` | RSA-SHA256 webhook verification, `p8_` secret patterns, scope least-privilege |
| S11 | `adobe-prod-checklist` | Go-live checklist: credential validation, health checks, canary rollout |
| S12 | `adobe-upgrade-migration` | JWT-to-OAuth migration, PDF SDK v3-to-v4, Photoshop cutout-to-v2 |

### Pro (P13-P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `adobe-ci-integration` | GitHub Actions: credential injection, secret scanning, integration tests |
| P14 | `adobe-deploy-integration` | Deploy to App Builder, Vercel, and Cloud Run with secret management |
| P15 | `adobe-webhooks-events` | I/O Events registration API, challenge handshake, RSA-SHA256 verification |
| P16 | `adobe-performance-tuning` | Token caching, parallel async jobs, adaptive polling, connection keep-alive |
| P17 | `adobe-cost-tuning` | Per-API pricing models, prompt hash caching, PDF transaction tracking |
| P18 | `adobe-reference-architecture` | Layered project structure for multi-API Adobe integrations |

### Flagship (F19-F24)

| # | Skill | What It Does |
|---|-------|-------------|
| F19 | `adobe-multi-env-setup` | Separate Console projects per env, GCP/AWS/Vault secret management |
| F20 | `adobe-observability` | Prometheus metrics, OpenTelemetry traces, alert rules per Adobe API |
| F21 | `adobe-incident-runbook` | Triage commands, decision tree, recovery procedures, postmortem template |
| F22 | `adobe-data-handling` | PII detection in PDF extractions, Firefly content policy, Privacy Service API |
| F23 | `adobe-enterprise-rbac` | Admin Console SCIM sync, UMAPI user management, product profile RBAC |
| F24 | `adobe-migration-deep-dive` | Strangler fig from competitors, API consolidation, adapter pattern |

### Flagship+ (X25-X30)

| # | Skill | What It Does |
|---|-------|-------------|
| X25 | `adobe-advanced-troubleshooting` | IMS token introspection, verbose HTTP tracing, layer-by-layer isolation |
| X26 | `adobe-load-scale` | k6 load tests for Firefly/PDF APIs, Kubernetes HPA, capacity planning |
| X27 | `adobe-reliability-patterns` | Per-API circuit breakers, graceful degradation, dead letter queues |
| X28 | `adobe-policy-guardrails` | `p8_` credential scanning, Firefly prompt pre-screening, quota enforcement |
| X29 | `adobe-architecture-variants` | Three blueprints: direct SDK, App Builder, dedicated microservice |
| X30 | `adobe-known-pitfalls` | 10 anti-patterns with real code: JWT auth, sync Firefly, leaked secrets |

## Key Adobe Endpoints

| Endpoint | Purpose |
|----------|---------|
| `ims-na1.adobelogin.com/ims/token/v3` | OAuth Server-to-Server token generation |
| `firefly-api.adobe.io/v3/images/generate` | Firefly text-to-image (sync) |
| `firefly-api.adobe.io/v3/images/generate-async` | Firefly text-to-image (async) |
| `firefly-api.adobe.io/v3/images/fill` | Generative fill (inpainting) |
| `firefly-api.adobe.io/v3/images/expand` | Image expansion (outpainting) |
| `image.adobe.io/v2/remove-background` | Photoshop background removal (v2) |
| `pdf-services.adobe.io` | PDF Services API |
| `static.adobeioevents.com` | I/O Events public keys for signature verification |

## Key npm Packages

```bash
@adobe/pdfservices-node-sdk   # PDF create, extract, merge, document generation
@adobe/firefly-apis            # Firefly text-to-image, fill, expand
@adobe/photoshop-apis          # Photoshop remove background, smart objects, actions
@adobe/lightroom-apis          # Lightroom auto tone, presets
@adobe/aio-sdk                 # App Builder SDK
@adobe/aio-cli                 # CLI for App Builder (global install)
@adobe/aio-lib-events          # I/O Events SDK
```

## License

MIT
