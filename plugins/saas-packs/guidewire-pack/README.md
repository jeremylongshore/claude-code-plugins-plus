# Guidewire Skill Pack

> 24 production-ready Claude Code skills for Guidewire InsuranceSuite -- real Cloud API calls, Gosu patterns, and PolicyCenter/ClaimCenter/BillingCenter workflows.

## What This Is

A complete skill pack for building, deploying, and operating Guidewire InsuranceSuite integrations. Every skill contains real Guidewire Cloud API code: OAuth2 authentication via Guidewire Hub, policy lifecycle management, claims processing (FNOL through settlement), and Gosu server-side patterns. Uses actual Cloud API endpoints (`/account/v1/accounts`, `/job/v1/submissions`, `/claim/v1/claims`).

## Installation

```bash
/plugin install guidewire-pack@claude-code-plugins-plus
```

## Skills

### Standard Skills (S01-S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `guidewire-install-auth` | Guidewire Hub OAuth2, Cloud Console setup, JWT token acquisition |
| S02 | `guidewire-hello-world` | First API calls to PolicyCenter, ClaimCenter, BillingCenter |
| S03 | `guidewire-local-dev-loop` | Guidewire Studio, Gosu debugging, GUnit tests, local server |
| S04 | `guidewire-sdk-patterns` | REST API Client, Jutro Digital SDK, Gosu entity patterns |
| S05 | `guidewire-core-workflow-a` | Policy lifecycle: account -> submission -> quote -> bind -> issue |
| S06 | `guidewire-core-workflow-b` | Claims lifecycle: FNOL -> investigation -> reserve -> payment -> settle |
| S07 | `guidewire-common-errors` | Fix 400/401/403/404/409/422, Gosu exceptions, validation errors |
| S08 | `guidewire-debug-bundle` | Cloud API diagnostics, Gosu stack traces, GCC logs |
| S09 | `guidewire-rate-limits` | Cloud API quotas, batch endpoints, throttling management |
| S10 | `guidewire-security-basics` | OAuth2 JWT, API roles, Gosu secure coding, SAML SSO |
| S11 | `guidewire-prod-checklist` | Configuration promotion, GUnit tests, monitoring setup |
| S12 | `guidewire-upgrade-migration` | Version upgrades, Gosu migration, Cloud environment management |

### Pro Skills (P13-P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `guidewire-ci-integration` | Gosu compilation, GUnit tests, configuration deployment pipelines |
| P14 | `guidewire-deploy-integration` | GCC deployment, configuration packages, environment promotion |
| P15 | `guidewire-webhooks-events` | App Events, SQS/SNS consumers, event-driven integration |
| P16 | `guidewire-performance-tuning` | Gosu query optimization, batch processing, JVM tuning |
| P17 | `guidewire-cost-tuning` | License management, compute right-sizing, API optimization |
| P18 | `guidewire-reference-architecture` | Enterprise architecture with Jutro, DataHub, Integration Gateway |

### Flagship Skills (F19-F24)

| # | Skill | What It Does |
|---|-------|-------------|
| F19 | `guidewire-multi-env-setup` | Dev/staging/prod with GCC configuration promotion |
| F20 | `guidewire-observability` | GCC monitoring, log export, performance dashboards |
| F21 | `guidewire-incident-runbook` | Production triage, batch failure recovery, escalation |
| F22 | `guidewire-data-handling` | Entity management, data migration, GDPR purge rules |
| F23 | `guidewire-enterprise-rbac` | API roles, user permissions, AD/SAML group mapping |
| F24 | `guidewire-migration-deep-dive` | Self-managed to Cloud migration, data migration, cutover |

## Key Guidewire Concepts

- **InsuranceSuite**: PolicyCenter (policy admin) + ClaimCenter (claims) + BillingCenter (billing)
- **Cloud API**: RESTful APIs with Swagger 2.0, OAuth2 JWT auth via Guidewire Hub
- **Gosu**: JVM language for server-side business logic (custom rules, workflows, validations)
- **Jutro**: React-based Digital Platform for building insurance portals
- **GCC**: Guidewire Cloud Console for environment management, deployments, monitoring
- **API Roles**: Endpoint-level permissions configured in GCC > Identity & Access

## About Guidewire

Guidewire is the leading platform for P&C (Property & Casualty) insurance carriers:
- **PolicyCenter** -- Policy administration (quoting, binding, issuance, endorsements)
- **ClaimCenter** -- Claims management (FNOL through settlement)
- **BillingCenter** -- Premium billing and payment processing
- **Jutro Digital Platform** -- Modern frontend framework
- **Cloud Platform** -- Managed infrastructure, APIs, and DevOps

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Gosu Language](https://gosu-lang.github.io/)
- [Guidewire Cloud Console](https://gcc.guidewire.com/)

## License

MIT
