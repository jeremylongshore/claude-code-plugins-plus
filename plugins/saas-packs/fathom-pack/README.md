# Fathom Skill Pack

> 18 production-grade Claude Code skills for AI meeting intelligence with Fathom

## What Is Fathom?

[Fathom](https://fathom.video) is an AI meeting assistant that automatically records, transcribes, and summarizes video meetings. The platform provides:

- **AI meeting notes** with automatic summaries and action items
- **Full transcripts** with speaker identification and timestamps
- **Webhooks** for real-time meeting data delivery
- **CRM integrations** for automatic meeting logging to Salesforce, HubSpot, etc.
- **REST API** at `api.fathom.ai/external/v1` with `X-Api-Key` authentication

API keys are per-user and can access meetings you recorded or that were shared to your team. Rate limit: 60 requests per minute. Webhooks deliver meeting data automatically when recordings are processed.

This skill pack provides real API calls and webhook patterns for every stage of Fathom integration.

## Installation

```bash
/plugin install fathom-pack@claude-code-plugins-plus
```

## Skills Included

### Getting Started (S01-S04)

| Skill | Description |
|-------|-------------|
| `fathom-install-auth` | API key generation, environment setup, OAuth for public apps |
| `fathom-hello-world` | List meetings, get transcripts, retrieve summaries and action items |
| `fathom-local-dev-loop` | Mock meeting data, test processors, development scripts |
| `fathom-sdk-patterns` | Python and TypeScript API clients with typed responses |

### Core Workflows (S05-S08)

| Skill | Description |
|-------|-------------|
| `fathom-core-workflow-a` | Meeting analytics pipeline: batch export, action item extraction |
| `fathom-core-workflow-b` | CRM sync, automated follow-up emails, meeting history database |
| `fathom-common-errors` | Auth failures, empty transcripts, webhook issues, rate limits |
| `fathom-debug-bundle` | API diagnostics for support cases |

### Operations (S09-S12)

| Skill | Description |
|-------|-------------|
| `fathom-rate-limits` | 60 req/min limit handling, batch processing patterns |
| `fathom-security-basics` | API key management, meeting data PII handling |
| `fathom-prod-checklist` | Production readiness for meeting integrations |
| `fathom-upgrade-migration` | API version tracking and schema change detection |

### Pro Skills (P13-P18)

| Skill | Description |
|-------|-------------|
| `fathom-ci-integration` | GitHub Actions for integration testing |
| `fathom-deploy-integration` | Cloud Function webhook handlers |
| `fathom-webhooks-events` | Webhook configuration, payload handling, real-time processing |
| `fathom-performance-tuning` | Caching, batch processing within rate limits |
| `fathom-cost-tuning` | Plan comparison, API optimization strategies |
| `fathom-reference-architecture` | Meeting intelligence platform architecture |

## Quick Start

### 1. Install the Pack

```bash
/plugin install fathom-pack@claude-code-plugins-plus
```

### 2. Get Your API Key

Go to [fathom.video](https://fathom.video) > **Settings** > **Integrations** > **API Access** and generate a key.

### 3. Fetch Your First Meeting

```bash
export FATHOM_API_KEY="your-key"

curl -s -H "X-Api-Key: ${FATHOM_API_KEY}" \
  "https://api.fathom.ai/external/v1/meetings?limit=1&include_summary=true" \
  | jq '.meetings[0] | {title, summary, action_items}'
```

### 4. Set Up Webhooks

Follow `fathom-webhooks-events` to receive real-time meeting data automatically.

## Key Fathom Links

- [Fathom API Documentation](https://developers.fathom.ai) -- full API reference
- [Fathom Quickstart](https://developers.fathom.ai/quickstart) -- getting started guide
- [Fathom Webhooks](https://developers.fathom.ai/webhooks) -- webhook setup
- [Fathom Help Center](https://help.fathom.video) -- troubleshooting and FAQs
- [Fathom Integrations](https://fathom.video/integrations) -- native CRM integrations
- [Fathom Pricing](https://fathom.video/pricing) -- free and team plans

## License

MIT
