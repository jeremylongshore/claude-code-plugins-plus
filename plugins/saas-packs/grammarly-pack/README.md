# Grammarly Skill Pack

> Claude Code skill pack for Grammarly API integration (24 skills)

## What It Does

Gives Claude Code deep knowledge of Grammarly's Writing Score API, AI Detection API, and Plagiarism Detection API. Skills cover OAuth 2.0 client credentials auth, document scoring with quality gates, AI content detection, plagiarism checking, and enterprise multi-team governance.

## Installation

```bash
/plugin install grammarly-pack@claude-code-plugins-plus
```

## Skills

### Standard Skills (S01-S12)

| Skill | What It Does |
|-------|-------------|
| `grammarly-install-auth` | OAuth 2.0 client credentials, token management |
| `grammarly-hello-world` | Score text, detect AI, check plagiarism |
| `grammarly-local-dev-loop` | Mocked tests, project structure |
| `grammarly-sdk-patterns` | Typed client with auto-auth, text chunking, Python client |
| `grammarly-core-workflow-a` | Writing Score API: batch scoring, quality threshold gates |
| `grammarly-core-workflow-b` | AI Detection + Plagiarism Detection: combined content audit |
| `grammarly-common-errors` | Fix 400/401/413/429 errors, plagiarism timeouts |
| `grammarly-debug-bundle` | API connectivity test, diagnostic bundle |
| `grammarly-rate-limits` | Exponential backoff, queue-based processing |
| `grammarly-security-basics` | Credential management, token lifecycle |
| `grammarly-prod-checklist` | Auth, integration, quality gates, monitoring checklist |
| `grammarly-upgrade-migration` | API version tracking, endpoint migration |

### Pro Skills (P13-P18)

| Skill | What It Does |
|-------|-------------|
| `grammarly-ci-integration` | GitHub Actions content quality gate |
| `grammarly-deploy-integration` | Vercel serverless scoring endpoint |
| `grammarly-webhooks-events` | Plagiarism polling callbacks, event bus pattern |
| `grammarly-performance-tuning` | Score caching, parallel API calls |
| `grammarly-cost-tuning` | Usage tracking, sample-based scoring |
| `grammarly-reference-architecture` | Full content quality pipeline architecture |

### Enterprise Skills (E19-E24)

| Skill | What It Does |
|-------|-------------|
| `grammarly-data-handling` | Text chunking, score aggregation, file processing |
| `grammarly-enterprise-rbac` | Team credentials, scope-based access control |
| `grammarly-incident-runbook` | API outage triage, severity classification, fallback mode |
| `grammarly-migration-deep-dive` | Text Editor SDK deprecation to REST API migration |
| `grammarly-multi-env-setup` | Dev/staging/prod credential isolation |
| `grammarly-observability` | API metrics, structured logging, alerting |

## Key Concepts

- **Writing Score API** (`/v2/scores`) — overall score + engagement, correctness, clarity, tone
- **AI Detection API** (`/v1/ai-detection`) — 0-100 score for AI-generated content
- **Plagiarism Detection API** (`/v1/plagiarism`) — async, poll for results
- **Limits**: min 30 words, max 100K chars (4 MB)
- **Auth**: OAuth 2.0 client credentials grant via `api.grammarly.com`

## License

MIT
