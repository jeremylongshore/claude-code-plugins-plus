---
name: documenso-cost-tuning
description: |
  Optimize Documenso usage costs and manage subscription efficiency.
  Use when analyzing costs, optimizing document usage,
  or managing Documenso subscription tiers.
  Trigger with phrases like "documenso costs", "documenso pricing",
  "optimize documenso spending", "documenso usage".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, cost-optimization]

---
# Documenso Cost Tuning

## Overview

Optimize Documenso costs through plan selection, template reuse, self-hosting, and usage monitoring. Documenso's pricing is uniquely developer-friendly: paid plans include unlimited API usage and signing volume.

## Prerequisites

- Documenso account with billing access
- Understanding of your document volume patterns

## Documenso Pricing Model

| Plan | Price | Documents | API / Signing | Teams | Key Feature |
|------|-------|-----------|---------------|-------|-------------|
| Free | $0/mo | Limited | Fair use | No | Personal use |
| Individual | $30/mo (early adopter) | Unlimited | Unlimited | No | Full API access |
| Team | $30/mo+ | Unlimited | Unlimited | Yes, unlimited | Team management, webhooks |
| Enterprise | Custom ($30K+/yr self-hosted) | Unlimited | Unlimited | Yes | SSO, audit logs, compliance |
| Self-Hosted (AGPL) | Free | Unlimited | No limits | Community | Full control, no SLA |

**Key insight:** Documenso does not charge per API call or per document on paid plans. Cost optimization is about choosing the right plan tier, not reducing API usage.

## Instructions

### Step 1: Right-Size Your Plan

```text
Decision tree:
1. Personal use, < 5 docs/month? → Free tier
2. Individual developer, unlimited docs? → Individual ($30/mo)
3. Multiple team members collaborating? → Team plan
4. Need SSO, audit logs, or compliance? → Enterprise
5. Want full control, have DevOps capacity? → Self-host (AGPL, free)
```

### Step 2: Template Reuse to Save Time (Not Money)

Templates don't save money (paid plans are unlimited), but they save developer time and reduce errors:

```typescript
// WITHOUT templates: rebuild every time (slow, error-prone)
async function createContractManual(client: Documenso, signer: Signer) {
  const doc = await client.documents.createV0({ title: `Contract — ${signer.name}` });
  // Upload PDF, add recipient, add 6 fields... every time
  // 7+ API calls per document
}

// WITH templates: one API call + send
async function createContractFromTemplate(templateId: number, signer: Signer) {
  const res = await fetch(
    `https://app.documenso.com/api/v1/templates/${templateId}/create-document`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.DOCUMENSO_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: `Contract — ${signer.name}`,
        recipients: [{ email: signer.email, name: signer.name, role: "SIGNER" }],
      }),
    }
  );
  const doc = await res.json();
  // One call to create, one to send = 2 API calls
  await fetch(`https://app.documenso.com/api/v1/documents/${doc.documentId}/send`, {
    method: "POST",
    headers: { Authorization: `Bearer ${process.env.DOCUMENSO_API_KEY}` },
  });
  return doc;
}
```

### Step 3: Self-Hosted Cost Analysis

```text
Self-hosted (AGPL license, free for commercial use):
  Server: ~$20/mo (small VPS with Docker)
  Database: Included (PostgreSQL in Docker)
  Email: ~$5/mo (Mailgun, Resend, etc.)
  SSL: Free (Let's Encrypt)
  Total: ~$25/mo for unlimited everything

vs. Cloud Team plan: $30/mo+

Self-host makes sense when:
  - You need data sovereignty (documents never leave your infra)
  - You want zero vendor lock-in
  - You have DevOps capacity to maintain it
  - You need custom branding / white-labeling
```

### Step 4: Monitor Usage Patterns

```typescript
// Track document creation patterns for capacity planning
async function getUsageStats(client: Documenso) {
  const { documents } = await client.documents.findV0({
    page: 1,
    perPage: 100,
    orderByColumn: "createdAt",
    orderByDirection: "desc",
  });

  const now = new Date();
  const thisMonth = documents.filter(
    (d: any) => new Date(d.createdAt).getMonth() === now.getMonth()
  );

  const byStatus = thisMonth.reduce((acc: Record<string, number>, d: any) => {
    acc[d.status] = (acc[d.status] || 0) + 1;
    return acc;
  }, {});

  console.log(`This month: ${thisMonth.length} documents`);
  console.log(`By status:`, byStatus);
  console.log(`Completion rate: ${((byStatus.COMPLETED || 0) / thisMonth.length * 100).toFixed(0)}%`);
}
```

### Step 5: Reduce Waste

```text
Cost waste patterns (time-based, not money-based on unlimited plans):
1. Abandoned drafts → Set up cleanup script to delete old DRAFT documents
2. Duplicate documents → Use templates instead of manual creation
3. Failed sends → Validate recipient emails before creating documents
4. Test data in production → Use staging environment for development
```

## Error Handling

| Cost Issue | Indicator | Solution |
|------------|-----------|----------|
| Overage on free plan | Document limit reached | Upgrade to Individual ($30/mo) |
| Unused team seats | Low active user count | Audit team members quarterly |
| Self-hosted high infra cost | Oversized server | Right-size: Documenso runs on 1 vCPU / 2GB RAM |
| Abandoned drafts consuming storage | Many DRAFT status docs | Schedule cleanup script |

## Resources

- [Documenso Pricing](https://documenso.com/pricing)
- [Self-Hosting Guide](https://docs.documenso.com/developers/self-hosting)
- [Template Best Practices](https://docs.documenso.com/users/templates)
- [Fair Use Policy](https://docs.documenso.com/users/fair-use)

## Next Steps

For architecture patterns, see `documenso-reference-architecture`.
