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
| `claude-install-auth` | Install and configure the Anthropic SDK for Claude API access |
| `claude-hello-world` | First Claude API call — messages, streaming, and basic parameters |
| `claude-local-dev-loop` | Local development workflow with hot reload and request logging |
| `claude-sdk-patterns` | Production SDK patterns — retries, timeouts, TypeScript types |
| `claude-model-inference` | Model selection, parameters, and inference optimization |
| `claude-embeddings-search` | Embeddings generation and semantic search with Voyage AI |
| `claude-common-errors` | Diagnose and fix common Anthropic API errors |
| `claude-debug-bundle` | Collect diagnostic data for Anthropic support tickets |
| `claude-rate-limits` | Understand and handle rate limits (RPM, TPM, TPD) |
| `claude-security-basics` | API key security, secret rotation, and access controls |
| `claude-prod-checklist` | Production readiness checklist for Claude deployments |
| `claude-upgrade-migration` | Migrate between SDK versions and API changes |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `claude-ci-integration` | CI/CD pipeline integration with Claude API |
| `claude-deploy-integration` | Deploy Claude-powered apps to production |
| `claude-webhooks-events` | Handle Anthropic webhooks and event streams |
| `claude-performance-tuning` | Optimize latency, throughput, and token usage |
| `claude-cost-tuning` | Token cost optimization and budget management |
| `claude-reference-architecture` | Reference architectures for Claude-powered systems |

### Flagship Skills (F19-F24)
| Skill | Description |
|-------|-------------|
| `claude-multi-env-setup` | Multi-environment configuration (dev/staging/prod) |
| `claude-observability` | Logging, tracing, and monitoring for Claude API calls |
| `claude-incident-runbook` | Incident response runbooks for Claude API outages |
| `claude-data-handling` | Data privacy, PII handling, and content filtering |
| `claude-enterprise-rbac` | Enterprise RBAC and workspace management |
| `claude-migration-deep-dive` | Complex migration scenarios and data transformation |

### Flagship+ Skills (X25-X30)
| Skill | Description |
|-------|-------------|
| `claude-advanced-troubleshooting` | Advanced debugging for complex API issues |
| `claude-load-scale` | Load testing and horizontal scaling patterns |
| `claude-reliability-patterns` | Circuit breakers, fallbacks, and resilience patterns |
| `claude-policy-guardrails` | Content policy, guardrails, and safety configuration |
| `claude-architecture-variants` | Architecture patterns — RAG, agents, tool use, multi-turn |
| `claude-known-pitfalls` | Known pitfalls and anti-patterns to avoid |

### Bonus Skills
| Skill | Description |
|-------|-------------|
| `claude-core-workflow-a` | Core API workflow — messages, streaming, system prompts |
| `claude-core-workflow-b` | Advanced workflow — tool use, vision, and structured output |

## Usage

Skills trigger automatically when you discuss Claude API topics. For example:

- "Help me set up the Claude API" → triggers `claude-install-auth`
- "Debug this Anthropic error" → triggers `claude-common-errors`
- "Deploy my Claude integration" → triggers `claude-deploy-integration`

## License

MIT
