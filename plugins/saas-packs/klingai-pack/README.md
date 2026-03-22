# Kling AI Skill Pack

30 production-ready skills for [Kling AI](https://klingai.com/) -- the leading AI video generation platform by Kuaishou Technology. Covers the full API surface: text-to-video, image-to-video, video extension, lip sync, effects, camera control, motion brush, virtual try-on, and Kolors image generation.

**API Base URL:** `https://api.klingai.com/v1`
**Auth:** JWT tokens from Access Key (AK) + Secret Key (SK), 30-minute expiry, HS256 signing.

---

## One-Pager

### The Problem

Kling AI's API uses JWT authentication (not simple API keys), has async task-based generation (submit, poll, download), temporary CDN URLs that expire, mutually exclusive feature sets for image-to-video, and model versions with different capability matrices. Getting all of this right requires reading across fragmented docs and multiple community examples.

### The Solution

30 Claude Code skills with real Kling AI API endpoints, real request/response shapes, real Python and Node.js code, real error codes, and real cost calculations. Every skill uses the actual `https://api.klingai.com/v1` base URL and actual JWT authentication patterns. No placeholder code.

### What's Included

| Category | Skills | Coverage |
|----------|--------|----------|
| **Onboarding** | 6 | Auth setup, hello world, model catalog, SDK patterns, T2V basics, pricing |
| **Operations** | 6 | Error diagnosis, debug logging, rate limits, job monitoring, prod checklist, version migration |
| **CI/CD & Pipelines** | 6 | Webhooks, batch processing, async workflows, cloud storage, CI/CD, reference architecture |
| **Enterprise** | 6 | Team access, cost controls, usage analytics, content policy, audit logging, compliance review |
| **Advanced** | 6 | Image-to-video, video extension, camera control, style/effects, performance tuning, pitfalls |

### Stack

| Component | Technology |
|-----------|-----------|
| API | REST over HTTPS, JWT auth (HS256) |
| Models | kling-v1 through kling-v2-6, Kolors v1.5-v2.1 |
| Languages | Python 3.8+ (PyJWT, requests), Node.js 18+ (jsonwebtoken) |
| Features | T2V, I2V, video extend, lip sync, effects, camera control, motion brush, virtual try-on |
| Pricing | Credit-based: 10 credits/5s standard, 35 credits/5s professional |

### Key Differentiators

- **Real JWT auth code** -- not "set your API key" placeholder, but actual `jwt.encode()` with correct headers, payload, and auto-refresh
- **Actual API endpoints** -- every skill uses `https://api.klingai.com/v1/videos/text2video`, `/image2video`, `/video-extend`, `/effects`, `/lip-sync`
- **Complete task lifecycle** -- submit, poll with adaptive backoff, handle succeed/failed states, download, store
- **Cost-aware** -- credit calculations for every model/mode/duration combo including the 5x audio multiplier
- **Production patterns** -- connection pooling, rate limiting, budget guards, batch queues, webhook fallback

---

## Skill Index

### Onboarding & Foundations
| Skill | What It Does |
|-------|-------------|
| `klingai-install-auth` | JWT authentication setup with AK/SK, auto-refresh token manager |
| `klingai-hello-world` | Minimal 20-line generate-poll-download example |
| `klingai-model-catalog` | All models (v1-v2.6), Kolors, specialty models, decision tree |
| `klingai-sdk-patterns` | Production client wrapper with typed models, retry, async polling |
| `klingai-text-to-video` | Full T2V with camera control, negative prompts, native audio |
| `klingai-pricing-basics` | Credit costs, subscription plans, API packs, cost estimation |

### Operations & Debugging
| Skill | What It Does |
|-------|-------------|
| `klingai-common-errors` | HTTP + task-level error reference with tested fixes |
| `klingai-debug-bundle` | Structured logging, request tracing, diagnostic script |
| `klingai-rate-limits` | Backoff with jitter, concurrent task limiter, request queue |
| `klingai-job-monitoring` | Batch tracker, stuck task detection, adaptive polling |
| `klingai-prod-checklist` | 40-point checklist: auth, errors, cost, security, monitoring |
| `klingai-upgrade-migration` | Version history, breaking changes, A/B comparison, rollback |

### CI/CD & Deployment
| Skill | What It Does |
|-------|-------------|
| `klingai-webhook-config` | Callback URL setup, Flask/Express receivers, reliability fallback |
| `klingai-batch-processing` | Rate-limited batch submission, async gather, callback batches |
| `klingai-async-workflows` | Redis queue, state machine, multi-step pipeline, event-driven |
| `klingai-storage-integration` | Download + upload to S3, GCS, Azure Blob with metadata |
| `klingai-ci-integration` | GitHub Actions, GitLab CI, YAML-driven batch generation |
| `klingai-reference-architecture` | API gateway, worker pool, queue, storage, Docker Compose |

### Enterprise & Compliance
| Skill | What It Does |
|-------|-------------|
| `klingai-team-setup` | Per-project keys, role-based quotas, secrets manager integration |
| `klingai-cost-controls` | Budget guard, threshold alerts, pre-batch validation |
| `klingai-usage-analytics` | JSONL event logger, daily reports, cost analysis, CSV export |
| `klingai-content-policy` | Pre-submission prompt filter, safe negative prompts, rejection handler |
| `klingai-audit-logging` | Tamper-evident chain logging, integrity verification, audit reports |
| `klingai-compliance-review` | Security checklist, GDPR handler, automated compliance check |

### Advanced Patterns
| Skill | What It Does |
|-------|-------------|
| `klingai-image-to-video` | I2V with motion brush, static masks, start-to-end transitions |
| `klingai-video-extension` | Chain extensions to build 20s+ videos from 5s clips |
| `klingai-camera-control` | Pan, tilt, zoom, roll, dolly with intensity guidelines |
| `klingai-style-transfer` | Prompt-based styling, Effects API, Kolors restyle, cfg_scale tuning |
| `klingai-performance-tuning` | Benchmarking, connection pooling, prompt optimization, caching |
| `klingai-known-pitfalls` | 10 documented gotchas with symptoms and tested fixes |

## Installation

```bash
# Claude Code Plugin
/plugin install klingai-pack@claude-code-plugins-plus

# npm
npm install @intentsolutionsio/klingai-pack
```

## Quick Start

```bash
export KLING_ACCESS_KEY="ak_your_key"
export KLING_SECRET_KEY="sk_your_key"
```

Then ask Claude: "Generate a 5-second video of a sunset over the ocean using Kling AI"

## Requirements

- Kling AI account with API access ([app.klingai.com/global/dev](https://app.klingai.com/global/dev))
- Access Key + Secret Key pair
- Python 3.8+ with `PyJWT` and `requests`, or Node.js 18+ with `jsonwebtoken`

## Resources

- [Kling AI Developer Portal](https://app.klingai.com/global/dev)
- [API Reference](https://app.klingai.com/global/dev/document-api/apiReference/model/textToVideo)
- [API Key Management](https://app.klingai.com/global/dev/api-key)
- [Pricing & Resource Packs](https://app.klingai.com/global/dev/document-api/productBilling/prePaidResourcePackage)

## License

MIT License -- see [LICENSE](LICENSE) for details.
