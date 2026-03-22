# Claude Skill Pack

> Claude Code skill pack for building with the Claude API and Anthropic SDK (32 skills)

## Installation

```bash
/plugin install claude-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)
| Skill | Description |
|-------|-------------|
| `clade-install-auth` | Install and configure the Anthropic SDK for Claude API access |
| `clade-hello-world` | First Claude API call — messages, streaming, and basic parameters |
| `clade-local-dev-loop` | Local development workflow with hot reload and request logging |
| `clade-sdk-patterns` | Production SDK patterns — retries, timeouts, TypeScript types |
| `clade-model-inference` | Model selection, parameters, and inference optimization |
| `clade-embeddings-search` | Embeddings generation and semantic search with Voyage AI |
| `clade-common-errors` | Diagnose and fix common Anthropic API errors |
| `clade-debug-bundle` | Collect diagnostic data for Anthropic support tickets |
| `clade-rate-limits` | Understand and handle rate limits (RPM, TPM, TPD) |
| `clade-security-basics` | API key security, secret rotation, and access controls |
| `clade-prod-checklist` | Production readiness checklist for Claude deployments |
| `clade-upgrade-migration` | Migrate between SDK versions and API changes |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `clade-ci-integration` | CI/CD pipeline integration with Claude API |
| `clade-deploy-integration` | Deploy Claude-powered apps to production |
| `clade-webhooks-events` | Handle Anthropic webhooks and event streams |
| `clade-performance-tuning` | Optimize latency, throughput, and token usage |
| `clade-cost-tuning` | Token cost optimization and budget management |
| `clade-reference-architecture` | Reference architectures for Claude-powered systems |

### Flagship Skills (F19-F24)
| Skill | Description |
|-------|-------------|
| `clade-multi-env-setup` | Multi-environment configuration (dev/staging/prod) |
| `clade-observability` | Logging, tracing, and monitoring for Claude API calls |
| `clade-incident-runbook` | Incident response runbooks for Claude API outages |
| `clade-data-handling` | Data privacy, PII handling, and content filtering |
| `clade-enterprise-rbac` | Enterprise RBAC and workspace management |
| `clade-migration-deep-dive` | Complex migration scenarios and data transformation |

### Flagship+ Skills (X25-X30)
| Skill | Description |
|-------|-------------|
| `clade-advanced-troubleshooting` | Advanced debugging for complex API issues |
| `clade-load-scale` | Load testing and horizontal scaling patterns |
| `clade-reliability-patterns` | Circuit breakers, fallbacks, and resilience patterns |
| `clade-policy-guardrails` | Content policy, guardrails, and safety configuration |
| `clade-architecture-variants` | Architecture patterns — RAG, agents, tool use, multi-turn |
| `clade-known-pitfalls` | Known pitfalls and anti-patterns to avoid |

### Bonus Skills
| Skill | Description |
|-------|-------------|
| `clade-core-workflow-a` | Core API workflow — messages, streaming, system prompts |
| `clade-core-workflow-b` | Advanced workflow — tool use, vision, and structured output |

## Usage

Skills trigger automatically when you discuss Claude API topics. For example:

- "Help me set up the Claude API" → triggers `clade-install-auth`
- "Debug this Anthropic error" → triggers `clade-common-errors`
- "Deploy my Claude integration" → triggers `clade-deploy-integration`

## License

MIT
