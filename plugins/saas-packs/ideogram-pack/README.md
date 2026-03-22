# Ideogram Skill Pack

> 24 Claude Code skills for Ideogram AI image generation -- text-to-image, editing, remixing, upscaling, and asset pipelines with real `api.ideogram.ai` endpoints.

Ideogram is an AI image generation API that excels at rendering legible text inside images -- a capability where most image models fail. This skill pack provides production-ready patterns for all six API endpoints: Generate, Edit (Magic Fill), Remix, Upscale, Describe, and Reframe.

**Links:** [Ideogram Developer Docs](https://developer.ideogram.ai) | [API Reference](https://developer.ideogram.ai/api-reference) | [Pricing](https://ideogram.ai/features/api-pricing) | [Tons of Skills](https://tonsofskills.com/learn/ideogram/)

---

## Installation

```bash
/plugin install ideogram-pack@claude-code-plugins-plus
```

## What This Pack Covers

| Capability | Endpoint | Skill |
|-----------|----------|-------|
| Text-to-image generation | `POST /generate` | `ideogram-core-workflow-a` |
| Image editing (Magic Fill) | `POST /v1/ideogram-v3/edit` | `ideogram-core-workflow-b` |
| Style transfer / remixing | `POST /v1/ideogram-v3/remix` | `ideogram-core-workflow-b` |
| Resolution upscaling | `POST /upscale` | `ideogram-core-workflow-b` |
| Image description | `POST /describe` | `ideogram-core-workflow-b` |
| Canvas reframing | `POST /v1/ideogram-v3/reframe` | `ideogram-core-workflow-b` |

## Skills Included

### Standard Skills (S01-S12)
| Skill | What It Does |
|-------|-------------|
| `ideogram-install-auth` | API key setup, authentication, billing configuration |
| `ideogram-hello-world` | First generation with curl, TypeScript, and Python |
| `ideogram-local-dev-loop` | Typed client, mock server, vitest tests |
| `ideogram-sdk-patterns` | Singleton, retry, Zod validation, multi-tenant factory |
| `ideogram-core-workflow-a` | Text-to-image: styles, aspect ratios, V3 presets, text rendering |
| `ideogram-core-workflow-b` | Edit, Remix, Upscale, Describe, Reframe with real endpoints |
| `ideogram-common-errors` | 401/422/429/400/402 diagnosis with fix scripts |
| `ideogram-debug-bundle` | Diagnostic tarball for support tickets |
| `ideogram-rate-limits` | Backoff, p-queue concurrency, token bucket |
| `ideogram-security-basics` | Key rotation, proxy pattern, pre-commit hooks |
| `ideogram-prod-checklist` | Pre-flight checks, health endpoints, rollback |
| `ideogram-upgrade-migration` | Legacy to V3 migration with enum mapping |

### Pro Skills (P13-P18)
| Skill | What It Does |
|-------|-------------|
| `ideogram-ci-integration` | GitHub Actions, mocked tests, prompt validation |
| `ideogram-deploy-integration` | Vercel, Cloud Run, Docker with S3 persistence |
| `ideogram-webhooks-events` | BullMQ queues, callbacks, batch pipelines |
| `ideogram-performance-tuning` | Speed tiers, prompt caching, parallel generation |
| `ideogram-cost-tuning` | Two-phase drafting, budget tracking, billing alerts |
| `ideogram-reference-architecture` | Prompt templates, asset pipelines, describe-then-remix |

### Flagship Skills (F19-F24)
| Skill | What It Does |
|-------|-------------|
| `ideogram-multi-env-setup` | Dev/staging/prod isolation with secret managers |
| `ideogram-observability` | Prometheus metrics, Grafana queries, alerting rules |
| `ideogram-incident-runbook` | Triage scripts, decision tree, fallback activation |
| `ideogram-data-handling` | Image persistence, metadata tracking, lifecycle cleanup |
| `ideogram-enterprise-rbac` | Team-scoped keys, content policies, budget enforcement |
| `ideogram-migration-deep-dive` | DALL-E/Midjourney to Ideogram with strangler fig pattern |

## API Quick Reference

**Base URL:** `https://api.ideogram.ai`
**Auth:** `Api-Key` header (not `Authorization: Bearer`)
**Rate Limit:** 10 in-flight requests (default)
**Image URLs:** Expire after ~1 hour -- download immediately

### Models (Legacy)
`V_1`, `V_1_TURBO`, `V_2`, `V_2_TURBO`, `V_2A`, `V_2A_TURBO`

### Style Types
Legacy: `AUTO`, `GENERAL`, `REALISTIC`, `DESIGN`, `RENDER_3D`, `ANIME`
V3: `AUTO`, `GENERAL`, `REALISTIC`, `DESIGN`, `FICTION`

### Aspect Ratios
Legacy: `ASPECT_1_1`, `ASPECT_16_9`, `ASPECT_9_16`, `ASPECT_3_2`, `ASPECT_2_3`, `ASPECT_4_3`, `ASPECT_3_4`, `ASPECT_10_16`, `ASPECT_16_10`, `ASPECT_1_3`, `ASPECT_3_1`
V3: `1x1`, `16x9`, `9x16`, `3x2`, `2x3`, `4x3`, `3x4`, `10x16`, `16x10`, `1x3`, `3x1`, `1x2`, `2x1`, `4x5`, `5x4`

### V3 Rendering Speeds
`FLASH` (fastest) | `TURBO` | `DEFAULT` | `QUALITY` (highest)

## Usage

Skills trigger automatically when you discuss Ideogram topics:

- "Help me set up Ideogram" -> `ideogram-install-auth`
- "Generate an image with text" -> `ideogram-core-workflow-a`
- "Edit this image with a mask" -> `ideogram-core-workflow-b`
- "Debug this Ideogram 422 error" -> `ideogram-common-errors`
- "Deploy my Ideogram integration" -> `ideogram-deploy-integration`

## License

MIT
