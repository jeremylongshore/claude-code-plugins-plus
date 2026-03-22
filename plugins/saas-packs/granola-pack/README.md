# Granola Skill Pack

> Claude Code skill pack for Granola AI meeting notes — 24 skills covering installation, templates, integrations, API access, security, enterprise deployment, and migration. Built on real Granola APIs, MCP, and Zapier automation.

## What is Granola?

Granola is an AI-powered meeting notepad that captures audio directly from your device — no bot joins your call. It transcribes via GPT-4o/Claude, merges your typed notes with the full transcript, and produces structured meeting notes with summaries, decisions, and action items. Works with Zoom, Google Meet, Teams, Slack Huddles, and WebEx.

**Key differentiator:** No recording bot visible to participants. Granola captures system audio locally, so attendees never see a "bot is recording" banner.

## Installation

```bash
/plugin install granola-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `granola-install-auth` | Install Granola, grant macOS/Windows audio permissions, connect Google/Outlook calendar |
| S02 | `granola-hello-world` | First meeting capture — notepad, Enhance Notes, Granola Chat, People & Companies |
| S03 | `granola-local-dev-loop` | Access meeting data via local cache (cache-v3.json), MCP server, or Enterprise API |
| S04 | `granola-sdk-patterns` | Zapier automation patterns, Enterprise API endpoints, multi-step workflow chains |
| S05 | `granola-core-workflow-a` | Template setup (29 built-in + custom), Recipes for Chat, pre-meeting context |
| S06 | `granola-core-workflow-b` | Post-meeting enhancement, sharing to Slack/Notion/CRM, follow-up emails |
| S07 | `granola-common-errors` | Audio capture failures, calendar sync issues, integration errors — platform-specific fixes |
| S08 | `granola-debug-bundle` | Diagnostic bundle for support — system info, audio config, network tests, cache metadata |
| S09 | `granola-rate-limits` | Plan comparison (Basic/Business/Enterprise), API rate limits, billing optimization |
| S10 | `granola-security-basics` | SOC 2 Type 2, AES-256/TLS 1.3, GDPR, recording consent, data architecture |
| S11 | `granola-prod-checklist` | Team rollout checklist — licensing, security, integrations, pilot program, go-live |
| S12 | `granola-upgrade-migration` | App version updates, plan upgrades/downgrades, seat management |

### Pro Skills (P13-P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `granola-ci-integration` | Zapier-to-GitHub Issues/Linear tasks pipeline, GitHub Actions meeting log |
| P14 | `granola-deploy-integration` | Native Slack, Notion, HubSpot, Attio, Affinity setup with auto-post and Zapier chains |
| P15 | `granola-webhooks-events` | Event-driven automation — Zapier triggers, webhook payloads, custom Express/FastAPI handlers |
| P16 | `granola-performance-tuning` | Audio optimization, meeting practices, template design, quality measurement |
| P17 | `granola-cost-tuning` | ROI calculation, plan selection, seat management, business case template |
| P18 | `granola-reference-architecture` | Enterprise architecture — pipeline topology, folder routing, security layers, DR |

### Flagship Skills (F19-F24)

| # | Skill | What It Does |
|---|-------|-------------|
| F19 | `granola-multi-env-setup` | Multi-workspace deployment with SSO/SCIM, per-workspace integrations, compliance controls |
| F20 | `granola-observability` | Analytics dashboards, BigQuery pipeline, automated Slack reports, health alerting |
| F21 | `granola-incident-runbook` | Incident triage (P1-P4), remediation per incident type, escalation path, post-incident review |
| F22 | `granola-data-handling` | Data export (cache + API), retention policies, GDPR SAR handling, archival workflows |
| F23 | `granola-enterprise-rbac` | Role hierarchy, SSO group mapping, sharing policies, audit logging, user lifecycle |
| F24 | `granola-migration-deep-dive` | Migration from Otter.ai/Fireflies/Fathom/tl;dv — export, parallel run, cutover |

## Real APIs and Integrations Covered

| Integration | Type | Plan Required |
|-------------|------|---------------|
| Slack | Native | Business |
| Notion | Native | Business |
| HubSpot | Native CRM | Business |
| Attio | Native CRM | Business |
| Affinity | Native CRM | Business |
| Zapier (8,000+ apps) | Automation | Business |
| MCP (Claude/Cursor) | AI agent protocol | Business |
| Enterprise API (REST) | Programmatic | Enterprise |
| Local cache (cache-v3.json) | Offline access | All (desktop app) |

## Granola Pricing (March 2026)

| Plan | Price | Key Features |
|------|-------|-------------|
| Basic | Free | 25 meetings lifetime, 14-day history |
| Business | $14/user/month | Unlimited meetings, all integrations, MCP, API |
| Enterprise | $35+/user/month | SSO, SCIM, analytics dashboard, full API, dedicated support |

## License

MIT
