# Podium Skill Pack

> Claude Code skill pack for Podium — business messaging, reviews management, payments, and webchat API integration (18 skills)

## What This Covers

Podium is a business communication platform for messaging, reviews, and payments. This pack covers the **Podium REST API** with OAuth2 authentication, messaging webhooks, review management, payment invoicing, and contact management.

**Key APIs:** Messages (webhook-driven), Contacts, Reviews, Payments/Invoices, Locations, Webhooks. Auth via OAuth2 (client_id + client_secret + authorization code).

## Installation

```bash
/plugin install podium-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)
| Skill | Description |
|-------|-------------|
| `podium-install-auth` | OAuth2 setup with client_id/secret, authorization code flow |
| `podium-hello-world` | Send first message, list contacts, check location |
| `podium-local-dev-loop` | Sandbox testing, ngrok for webhooks, mock message events |
| `podium-sdk-patterns` | API client wrapper, OAuth token refresh, error handling |
| `podium-core-workflow-a` | Messaging workflow: send/receive messages via webhooks |
| `podium-core-workflow-b` | Reviews and payments: request reviews, create invoices |
| `podium-common-errors` | Fix OAuth errors, webhook failures, message delivery issues |
| `podium-debug-bundle` | Collect API logs, webhook events, OAuth token state |
| `podium-rate-limits` | Handle API rate limits with backoff |
| `podium-security-basics` | OAuth credential management, webhook verification |
| `podium-prod-checklist` | Production deployment: HTTPS webhooks, monitoring, scopes |
| `podium-upgrade-migration` | API version changes and OAuth scope updates |

### Pro Skills (P13-P18)
| Skill | Description |
|-------|-------------|
| `podium-ci-integration` | CI pipeline with mocked Podium API tests |
| `podium-deploy-integration` | Deploy messaging service with secrets management |
| `podium-webhooks-events` | Handle message.sent, message.received, review.created events |
| `podium-performance-tuning` | Batch message operations, webhook processing optimization |
| `podium-cost-tuning` | Optimize API usage and message volume |
| `podium-reference-architecture` | Messaging service architecture with Podium integration |

## Usage

- "Set up Podium API" -- triggers `podium-install-auth`
- "Send a Podium message" -- triggers `podium-core-workflow-a`
- "Handle Podium webhook" -- triggers `podium-webhooks-events`

## Key Documentation

- [Podium Developer Portal](https://developer.podium.com/)
- [Getting Started](https://docs.podium.com/docs/getting-started)
- [OAuth2 Guide](https://docs.podium.com/docs/oauth)
- [Webhooks](https://docs.podium.com/docs/webhooks)

## License

MIT
