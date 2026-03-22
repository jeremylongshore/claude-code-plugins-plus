# Retell AI Skill Pack

> Claude Code skill pack for Retell AI — AI voice agents, phone call automation, LLM-powered conversations, and telephony integration (30 skills)

## What This Covers

Retell AI is a platform for building AI voice agents that handle phone calls. This pack covers the **Retell AI REST API** and **retell-sdk** for creating agents, managing phone calls, configuring LLM backends, handling call events via webhooks, and building custom voice workflows.

**Key APIs:** Agents (create, update, list), Calls (create phone call, list, get), Phone Numbers, LLM Configuration, Webhooks. Auth: `Authorization: Bearer <api_key>`. SDK: `retell-sdk` (npm).

## Installation

```bash
/plugin install retellai-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)
| Skill | Description |
|-------|-------------|
| `retellai-install-auth` | Install `retell-sdk`, configure API key |
| `retellai-hello-world` | Create first agent and make a test phone call |
| `retellai-local-dev-loop` | Local development with webhook tunneling |
| `retellai-sdk-patterns` | SDK client wrapper, typed responses, error handling |
| `retellai-core-workflow-a` | Agent creation: configure voice, LLM, and call flow |
| `retellai-core-workflow-b` | Phone call management: outbound calls, transfers, recordings |
| `retellai-common-errors` | Fix API errors, call failures, webhook issues |
| `retellai-debug-bundle` | Collect call logs, agent config, webhook traces |
| `retellai-rate-limits` | Handle API rate limits for call volume |
| `retellai-security-basics` | API key management, call recording security |
| `retellai-prod-checklist` | Production: phone numbers, monitoring, failover |
| `retellai-upgrade-migration` | SDK version upgrades |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `retellai-ci-integration` | CI pipeline with agent configuration tests |
| `retellai-deploy-integration` | Deploy voice agent service to production |
| `retellai-webhooks-events` | Handle call events: started, ended, transcript |
| `retellai-performance-tuning` | Optimize voice latency, concurrent calls |
| `retellai-cost-tuning` | Optimize per-minute costs, LLM selection |
| `retellai-reference-architecture` | Voice agent service architecture |

### Flagship Skills (F19-F30)
| Skill | Description |
|-------|-------------|
| `retellai-multi-env-setup` | Dev/staging/prod agent configurations |
| `retellai-observability` | Monitor call quality, latency, success rates |
| `retellai-incident-runbook` | Triage call failures and voice quality issues |
| `retellai-data-handling` | Call recording storage, transcript management |
| `retellai-enterprise-rbac` | Team access control and agent permissions |
| `retellai-migration-deep-dive` | Migrate from other telephony to Retell AI |
| `retellai-advanced-troubleshooting` | Debug voice quality, latency, and LLM issues |
| `retellai-architecture-variants` | Multi-agent, transfer, and IVR patterns |
| `retellai-known-pitfalls` | Common mistakes and anti-patterns |
| `retellai-load-scale` | Scale to high concurrent call volumes |
| `retellai-policy-guardrails` | Content filtering and compliance guardrails |
| `retellai-reliability-patterns` | Failover, retry, and redundancy patterns |

## Key Documentation

- [Retell AI Documentation](https://docs.retellai.com)
- [Create Phone Call](https://docs.retellai.com/api-references/create-phone-call)
- [retell-sdk on npm](https://www.npmjs.com/package/retell-sdk)
- [SDKs](https://docs.retellai.com/get-started/sdk)

## License

MIT
