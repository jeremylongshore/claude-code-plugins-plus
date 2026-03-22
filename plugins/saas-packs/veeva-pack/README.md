# Veeva Skill Pack

> 24 production-ready Claude Code skills for Veeva Vault -- real REST API, VQL queries, and VAPIL SDK code for life sciences.

## What This Is

A complete skill pack for integrating with Veeva Vault. Every skill contains real Vault REST API code: session authentication, VQL queries, document CRUD, lifecycle management, and clinical operations patterns. Built for life sciences teams working with regulatory documents, clinical trials, and quality management.

## Installation

```bash
/plugin install veeva-pack@claude-code-plugins-plus
```

## Skills

### Standard Skills (S01-S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `veeva-install-auth` | Session auth, VAPIL setup, VQL connection test |
| S02 | `veeva-hello-world` | Document CRUD, VQL queries, file upload |
| S03 | `veeva-local-dev-loop` | Sandbox environment, mock responses, VQL testing |
| S04 | `veeva-sdk-patterns` | VAPIL patterns, typed responses, session management |
| S05 | `veeva-core-workflow-a` | Document lifecycle, state transitions, approvals |
| S06 | `veeva-core-workflow-b` | Object CRUD, relationships, bulk operations |
| S07 | `veeva-common-errors` | Session expiry, VQL errors, permission issues |
| S08 | `veeva-debug-bundle` | Session diagnostics, API version check, VQL validation |
| S09 | `veeva-rate-limits` | API burst limits, bulk operation throttling |
| S10 | `veeva-security-basics` | Security profiles, session management, data access |
| S11 | `veeva-prod-checklist` | Validation, compliance checks, go-live requirements |
| S12 | `veeva-upgrade-migration` | API version migration, VQL changes, VAPIL updates |

### Pro + Flagship Skills (P13-F24)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `veeva-ci-integration` | Automated VQL validation, deployment pipelines |
| P14 | `veeva-deploy-integration` | Multi-vault deployment, configuration management |
| P15 | `veeva-webhooks-events` | Vault notifications, event-driven processing |
| P16 | `veeva-performance-tuning` | VQL optimization, bulk API, pagination |
| P17 | `veeva-cost-tuning` | API call optimization, bulk vs single operations |
| P18 | `veeva-reference-architecture` | Integration hub, ETL pipelines, clinical data flow |

## Key Concepts

- **Auth**: Session-based (POST /auth with username/password)
- **VQL**: SQL-like query language for Vault data retrieval
- **VAPIL**: Open-source Java SDK for all Platform APIs
- **Lifecycle**: Documents flow through regulated states
- **API Versioning**: `v24.1`, `v24.2`, etc. (versioned per release)

## License

MIT
