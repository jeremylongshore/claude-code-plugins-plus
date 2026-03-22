# Clari Skill Pack

> 18 production-grade Claude Code skills for revenue intelligence and forecast data pipelines with Clari

## What Is Clari?

[Clari](https://www.clari.com) is an enterprise revenue orchestration platform that provides AI-powered forecasting, pipeline management, and revenue intelligence. The platform offers:

- **Export API** (v4) for extracting forecast submissions, quota, adjustments, and CRM data
- **Copilot API** for conversation intelligence (call transcripts, coaching insights)
- **Revenue intelligence** with AI-driven deal inspection and pipeline analytics
- **Forecast submissions** tracking with historical change detection

The Clari Export API at `api.clari.com/v4` uses `apikey` header authentication. Export jobs are asynchronous -- you POST to start an export, poll for completion, then download results. This skill pack provides real API calls and production pipeline patterns for every stage of Clari integration.

## Installation

```bash
/plugin install clari-pack@claude-code-plugins-plus
```

## Skills Included

### Getting Started (S01-S04)

| Skill | Description |
|-------|-------------|
| `clari-install-auth` | API token generation, environment config, Copilot OAuth setup |
| `clari-hello-world` | First API calls: list forecasts, export data, check job status |
| `clari-local-dev-loop` | Mock forecast data, test pipeline locally, development scripts |
| `clari-sdk-patterns` | Python and TypeScript API client wrappers with job polling |

### Core Workflows (S05-S08)

| Skill | Description |
|-------|-------------|
| `clari-core-workflow-a` | Forecast export pipeline to Snowflake, BigQuery, or PostgreSQL |
| `clari-core-workflow-b` | Revenue analytics: accuracy tracking, pipeline coverage, change detection |
| `clari-common-errors` | Auth failures, empty exports, job timeouts, data mismatches |
| `clari-debug-bundle` | Collect API diagnostics for support cases |

### Operations (S09-S12)

| Skill | Description |
|-------|-------------|
| `clari-rate-limits` | Export polling backoff, sequential job scheduling |
| `clari-security-basics` | Token management, PII handling for exported data |
| `clari-prod-checklist` | Production readiness for forecast sync pipelines |
| `clari-upgrade-migration` | API version migration, schema change detection |

### Pro Skills (P13-P18)

| Skill | Description |
|-------|-------------|
| `clari-ci-integration` | GitHub Actions for pipeline testing and schema validation |
| `clari-deploy-integration` | Deploy to Airflow, Lambda, or Cloud Functions |
| `clari-webhooks-events` | Forecast change detection, Slack alerts, Copilot webhooks |
| `clari-performance-tuning` | Parallel exports, caching, incremental warehouse loads |
| `clari-cost-tuning` | Reduce API calls, optimize export frequency and data types |
| `clari-reference-architecture` | Data platform architecture with warehouse schema and analytics |

## Quick Start

### 1. Install the Pack

```bash
/plugin install clari-pack@claude-code-plugins-plus
```

### 2. Get Your API Token

Log in to [app.clari.com](https://app.clari.com), go to **User Settings > API Token**, and click **Generate New API Token**.

### 3. Export Your First Forecast

```python
import requests, os

api_key = os.environ["CLARI_API_KEY"]
headers = {"apikey": api_key, "Content-Type": "text/plain"}

# List forecasts
forecasts = requests.get(
    "https://api.clari.com/v4/export/forecast/list",
    headers=headers
).json()

print(f"Found {len(forecasts['forecasts'])} forecasts")
```

### 4. Build Your Pipeline

Follow `clari-core-workflow-a` to build a complete export-transform-load pipeline.

## Key Clari Links

- [Clari Developer Portal](https://developer.clari.com) -- API documentation
- [Clari API Reference](https://developer.clari.com/documentation/external_spec) -- endpoint spec
- [Clari Copilot API](https://api-doc.copilot.clari.com) -- conversation intelligence API
- [Clari Community](https://community.clari.com) -- community guides and tips
- [Clari Trust Center](https://www.clari.com/trust) -- security and compliance

## License

MIT
