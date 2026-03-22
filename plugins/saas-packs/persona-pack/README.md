# Persona Skill Pack

> Claude Code skill pack for Persona identity verification — KYC, inquiry flows, government ID verification, and webhook-driven verification pipelines (18 skills)

## What This Covers

Persona is an identity verification platform for KYC/AML compliance. This pack covers the **Persona REST API** for creating and managing inquiries, verification checks (government ID, selfie, database), webhook event handling, and embedding the Persona flow in web applications.

**Key APIs:** Inquiries (create, resume, list), Verifications (government ID, selfie, database), Accounts, Webhooks, Reports, API Keys. Auth via `Authorization: Bearer persona_<env>_xxx`.

## Installation

```bash
/plugin install persona-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)
| Skill | Description |
|-------|-------------|
| `persona-install-auth` | Configure API keys (`persona_sandbox_*` / `persona_production_*`), set up Bearer auth |
| `persona-hello-world` | Create your first inquiry, embed the Persona flow, check verification status |
| `persona-local-dev-loop` | Sandbox testing, ngrok for webhooks, mock verification responses |
| `persona-sdk-patterns` | API client wrapper, typed responses, pagination, error handling |
| `persona-core-workflow-a` | Full KYC flow: create inquiry template, embed flow, poll for completion |
| `persona-core-workflow-b` | Verification checks: government ID, selfie liveness, database lookups |
| `persona-common-errors` | Fix 401, 404, webhook signature failures, inquiry state errors |
| `persona-debug-bundle` | Collect inquiry IDs, API responses, webhook logs for support |
| `persona-rate-limits` | Handle 429 errors, implement backoff, queue verification requests |
| `persona-security-basics` | API key rotation, webhook secret management, PII handling |
| `persona-prod-checklist` | Go-live: production API keys, webhook HTTPS, compliance review |
| `persona-upgrade-migration` | API version upgrades, deprecated field migration |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `persona-ci-integration` | GitHub Actions with sandbox API testing, webhook simulation |
| `persona-deploy-integration` | Deploy verification service with secrets management |
| `persona-webhooks-events` | Handle inquiry.completed, verification.passed/failed events |
| `persona-performance-tuning` | Batch inquiry creation, parallel verification polling |
| `persona-cost-tuning` | Optimize verification costs with template selection and caching |
| `persona-reference-architecture` | KYC service architecture with Persona as verification provider |

## Usage

- "Set up Persona verification" -- triggers `persona-install-auth`
- "Create KYC inquiry" -- triggers `persona-core-workflow-a`
- "Handle Persona webhook" -- triggers `persona-webhooks-events`

## Key Documentation

- [Persona API Introduction](https://docs.withpersona.com/api-introduction)
- [API Quickstart](https://docs.withpersona.com/api-quickstart-tutorial)
- [Webhook Events](https://docs.withpersona.com/quickstart-webhooks)
- [API Keys](https://docs.withpersona.com/api-keys)

## License

MIT
