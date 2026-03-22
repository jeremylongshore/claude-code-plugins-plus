---
name: instantly-reference-architecture
description: |
  Implement Instantly.ai reference architecture with best-practice project layout.
  Use when designing new Instantly integrations, planning multi-campaign systems,
  or building an outreach automation platform.
  Trigger with phrases like "instantly architecture", "instantly project structure",
  "instantly reference design", "instantly system design", "instantly integration layout".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, architecture, design]

---
# Instantly Reference Architecture

## Overview
Reference architecture for production Instantly.ai integrations. Covers project layout, API client design, event-driven webhook processing, campaign management, lead pipeline, and analytics dashboard. Designed for teams building outreach automation on top of Instantly API v2.

## Architecture Diagram

```
                                     Instantly API v2
                                    (api.instantly.ai)
                                          |
                    ┌─────────────────────┼─────────────────────┐
                    |                     |                     |
              Campaign Mgmt         Lead Pipeline         Account Mgmt
              (create/launch/       (import/move/          (warmup/
               pause/analytics)      enrich/block)         vitals/pause)
                    |                     |                     |
                    └─────────┬───────────┘                    |
                              |                                |
                    ┌─────────┴─────────┐                     |
                    |   Your Backend    |◄────────────────────┘
                    |  (Node/Python)    |
                    └────────┬──────────┘
                             |
                    ┌────────┴──────────┐
                    |  Webhook Receiver |◄──── Instantly Webhooks
                    |  (Cloud Run /     |      (reply_received,
                    |   Vercel / Fly)   |       email_bounced, etc.)
                    └────────┬──────────┘
                             |
               ┌─────────────┼─────────────┐
               |             |             |
           CRM Sync     Slack Alerts   Analytics DB
```

## Project Layout

```
instantly-integration/
├── src/
│   ├── instantly/
│   │   ├── client.ts          # API client wrapper with retry + auth
│   │   ├── types.ts           # TypeScript interfaces for API schemas
│   │   ├── pagination.ts      # Cursor-based pagination helpers
│   │   └── cache.ts           # Analytics caching layer
│   ├── campaigns/
│   │   ├── create.ts          # Campaign creation with sequences
│   │   ├── launch.ts          # Campaign activation workflow
│   │   ├── analytics.ts       # Campaign performance tracking
│   │   └── templates.ts       # Email sequence templates
│   ├── leads/
│   │   ├── import.ts          # Lead import from CSV/CRM
│   │   ├── lists.ts           # Lead list management
│   │   ├── enrich.ts          # Lead enrichment pipeline
│   │   └── blocklist.ts       # Block list management
│   ├── accounts/
│   │   ├── warmup.ts          # Warmup enable/disable/monitor
│   │   ├── health.ts          # Account vitals testing
│   │   └── rotation.ts       # Account assignment to campaigns
│   ├── webhooks/
│   │   ├── server.ts          # Express webhook receiver
│   │   ├── handlers.ts        # Event type handlers
│   │   └── validation.ts     # Payload validation
│   └── config.ts              # Environment config
├── tests/
│   ├── unit/                  # Unit tests (mocked API)
│   ├── integration/           # Integration tests (mock server)
│   └── e2e/                   # End-to-end (live API, read-only)
├── scripts/
│   ├── seed-leads.ts          # Seed campaign with test leads
│   ├── audit.ts               # Workspace audit script
│   └── migrate-v1-to-v2.ts   # API migration helper
├── .env.example
├── .github/workflows/ci.yml
├── Dockerfile
├── package.json
└── tsconfig.json
```

## Core Module Implementation

### API Client (src/instantly/client.ts)
```typescript
import "dotenv/config";

export class InstantlyClient {
  constructor(
    private apiKey = process.env.INSTANTLY_API_KEY!,
    private baseUrl = "https://api.instantly.ai/api/v2"
  ) {}

  async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.apiKey}`,
        ...init.headers,
      },
    });

    if (res.status === 429) {
      await new Promise((r) => setTimeout(r, 2000));
      return this.request<T>(path, init);
    }

    if (!res.ok) {
      throw new InstantlyApiError(res.status, path, await res.text());
    }

    return res.json() as Promise<T>;
  }

  // Campaign operations
  campaigns = {
    list: (limit = 50) => this.request<Campaign[]>(`/campaigns?limit=${limit}`),
    get: (id: string) => this.request<Campaign>(`/campaigns/${id}`),
    create: (data: CreateCampaignInput) =>
      this.request<Campaign>("/campaigns", { method: "POST", body: JSON.stringify(data) }),
    activate: (id: string) =>
      this.request<void>(`/campaigns/${id}/activate`, { method: "POST" }),
    pause: (id: string) =>
      this.request<void>(`/campaigns/${id}/pause`, { method: "POST" }),
    analytics: (id: string) =>
      this.request<CampaignAnalytics>(`/campaigns/analytics?id=${id}`),
    analyticsDaily: (id: string, start: string, end: string) =>
      this.request(`/campaigns/analytics/daily?campaign_id=${id}&start_date=${start}&end_date=${end}`),
  };

  // Lead operations
  leads = {
    create: (data: CreateLeadInput) =>
      this.request<Lead>("/leads", { method: "POST", body: JSON.stringify(data) }),
    list: (filter: ListLeadsInput) =>
      this.request<Lead[]>("/leads/list", { method: "POST", body: JSON.stringify(filter) }),
    get: (id: string) => this.request<Lead>(`/leads/${id}`),
    delete: (id: string) => this.request(`/leads/${id}`, { method: "DELETE" }),
    updateInterest: (email: string, campaignId: string, value: number) =>
      this.request("/leads/update-interest-status", {
        method: "POST",
        body: JSON.stringify({ lead_email: email, campaign_id: campaignId, interest_value: value }),
      }),
  };

  // Account operations
  accounts = {
    list: (limit = 50) => this.request<Account[]>(`/accounts?limit=${limit}`),
    get: (email: string) => this.request<Account>(`/accounts/${encodeURIComponent(email)}`),
    enableWarmup: (emails: string[]) =>
      this.request("/accounts/warmup/enable", { method: "POST", body: JSON.stringify({ emails }) }),
    warmupAnalytics: (emails: string[]) =>
      this.request("/accounts/warmup-analytics", { method: "POST", body: JSON.stringify({ emails }) }),
    testVitals: (emails: string[]) =>
      this.request("/accounts/test/vitals", { method: "POST", body: JSON.stringify({ accounts: emails }) }),
    pause: (email: string) =>
      this.request(`/accounts/${encodeURIComponent(email)}/pause`, { method: "POST" }),
    resume: (email: string) =>
      this.request(`/accounts/${encodeURIComponent(email)}/resume`, { method: "POST" }),
  };

  // Webhook operations
  webhooks = {
    list: () => this.request<Webhook[]>("/webhooks?limit=50"),
    create: (data: CreateWebhookInput) =>
      this.request<Webhook>("/webhooks", { method: "POST", body: JSON.stringify(data) }),
    test: (id: string) => this.request(`/webhooks/${id}/test`, { method: "POST" }),
    delete: (id: string) => this.request(`/webhooks/${id}`, { method: "DELETE" }),
  };
}
```

### Campaign Template System (src/campaigns/templates.ts)
```typescript
export const SEQUENCE_TEMPLATES = {
  "3-step-cold": {
    name: "3-Step Cold Outreach",
    sequences: [{
      steps: [
        { type: "email" as const, delay: 0, variants: [
          { subject: "{{firstName}}, quick question about {{companyName}}", body: "..." },
        ]},
        { type: "email" as const, delay: 3, delay_unit: "days" as const, variants: [
          { subject: "Re: {{firstName}}, quick question", body: "..." },
        ]},
        { type: "email" as const, delay: 5, delay_unit: "days" as const, variants: [
          { subject: "Re: {{firstName}}, quick question", body: "..." },
        ]},
      ],
    }],
    defaults: {
      daily_limit: 50,
      stop_on_reply: true,
      email_gap: 120,
      link_tracking: false,
      open_tracking: true,
    },
  },

  "meeting-request": {
    name: "Meeting Request",
    sequences: [{
      steps: [
        { type: "email" as const, delay: 0, variants: [
          { subject: "15 min chat, {{firstName}}?", body: "..." },
        ]},
        { type: "email" as const, delay: 2, delay_unit: "days" as const, variants: [
          { subject: "Re: 15 min chat", body: "..." },
        ]},
      ],
    }],
    defaults: {
      daily_limit: 30,
      stop_on_reply: true,
      email_gap: 180,
    },
  },
};
```

## Data Flow Summary
```
Lead CSV/CRM → import.ts → POST /leads → Campaign
                                            ↓
                              POST /campaigns/{id}/activate
                                            ↓
                              Instantly sends emails
                                            ↓
                              Webhook events fire
                                            ↓
                              handlers.ts routes events
                                            ↓
                    ┌─────────┬─────────┬───────────┐
                    CRM       Slack     Analytics   Block List
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Client constructor fails | Missing `INSTANTLY_API_KEY` | Check `.env` file |
| Namespace methods fail | API scope mismatch | Verify key has correct scopes |
| Import fails midway | Network/rate limit | Batch with retry (see `instantly-performance-tuning`) |
| Webhook events missing | Webhook not registered | Register after deploy (see `instantly-webhooks-events`) |

## Resources
- [Instantly API v2 Docs](https://developer.instantly.ai/)
- [API Schemas](https://developer.instantly.ai/api/v2/schemas)
- [Instantly Help Center](https://help.instantly.ai)

## Next Steps
For multi-environment setup, see `instantly-multi-env-setup`.
