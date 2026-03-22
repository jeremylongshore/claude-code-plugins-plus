# Lindy AI Skill Pack

> 24 enterprise-grade skills for building, integrating, and operating Lindy AI agents — the no-code AI automation platform with 7,000+ integrations.

## What Lindy Is

Lindy AI is a no-code/low-code platform for building AI agents ("Lindies") that automate workflows across email, chat, Slack, phone, and 7,000+ app integrations via Pipedream. Agents consist of four components: **Prompt** (behavioral instructions), **Model** (GPT-4, Claude, Gemini), **Skills** (available actions), and **Exit Conditions** (completion criteria). Agents run on Lindy's managed infrastructure — you integrate via webhook triggers, HTTP Request actions, and optional SDKs.

**Key concepts**: Triggers wake agents (webhook, email, schedule, chat, Slack, calendar, agent delegation). Actions execute tasks (send email, post to Slack, update sheets, HTTP requests, Run Code in Python/JS via E2B sandbox). Conditions route workflows with natural language branching. Multi-agent "Societies of Lindies" enable modular delegation between specialized agents.

## Installation

```bash
/plugin install lindy-pack@claude-code-plugins-plus
```

## Skills (24)

### Standard (S01-S12)
| Skill | What It Covers |
|-------|---------------|
| `lindy-install-auth` | API keys, webhook secrets, SDK setup, plan tiers |
| `lindy-hello-world` | First agent: webhook trigger -> Slack notification |
| `lindy-local-dev-loop` | ngrok tunnels, webhook receivers, test harnesses |
| `lindy-sdk-patterns` | Webhook client, HTTP Request action, Run Code (E2B), callbacks |
| `lindy-core-workflow-a` | Agent creation, triggers, actions, conditions, knowledge base |
| `lindy-core-workflow-b` | Multi-trigger, scheduling, delegation, loops, linked actions |
| `lindy-common-errors` | Trigger failures, action errors, agent loops, KB issues |
| `lindy-debug-bundle` | Diagnostics, connectivity tests, decision tree, support bundles |
| `lindy-rate-limits` | Credit system, consumption by model, rate limiting, budget alerts |
| `lindy-security-basics` | Key management, webhook auth, agent scoping, enterprise features |
| `lindy-prod-checklist` | Go-live checklist, validation scripts, go/no-go criteria |
| `lindy-upgrade-migration` | Workspace migration, webhook reconfiguration, parallel runs |

### Pro (P13-P18)
| Skill | What It Covers |
|-------|---------------|
| `lindy-ci-integration` | GitHub Actions, webhook handler tests, smoke tests |
| `lindy-deploy-integration` | Docker, Vercel, post-deploy verification, rollback |
| `lindy-webhooks-events` | Inbound/outbound webhooks, callback pattern, trigger filters |
| `lindy-performance-tuning` | Model right-sizing, step consolidation, KB optimization |
| `lindy-cost-tuning` | Credit audit, model downgrades, trigger filtering, agent consolidation |
| `lindy-reference-architecture` | Webhook integration, event pipelines, multi-agent, chat+KB, scheduled |

### Flagship (F19-F24)
| Skill | What It Covers |
|-------|---------------|
| `lindy-multi-env-setup` | Workspace isolation, environment configs, secret management, CI/CD |
| `lindy-observability` | Task Completed triggers, Prometheus metrics, Grafana dashboards, evals |
| `lindy-incident-runbook` | Severity levels, diagnostic scripts, playbooks, escalation, post-incident |
| `lindy-data-handling` | PII controls, KB safety, memory rules, GDPR/CCPA/HIPAA compliance |
| `lindy-enterprise-rbac` | Workspace roles, folder permissions, SSO/SCIM, audit logs, offboarding |
| `lindy-migration-deep-dive` | Zapier/Make/n8n/LangChain migration, phased cutover, redesign patterns |

## Lindy Quick Reference

| Resource | URL |
|----------|-----|
| Dashboard | https://app.lindy.ai |
| Documentation | https://docs.lindy.ai |
| Academy | https://www.lindy.ai/academy-lessons/getting-started-101 |
| Integrations | https://www.lindy.ai/integrations |
| Status | https://status.lindy.ai |
| Pricing | https://www.lindy.ai/pricing |

## License

MIT
