---
name: guidewire-sdk-patterns
description: 'Master Guidewire SDK patterns: REST API Client, Jutro Digital SDK, and
  Gosu best practices.

  Trigger: "guidewire sdk patterns", "sdk-patterns".

  '
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- insurance
- guidewire
compatibility: Designed for Claude Code
---
# Guidewire SDK Patterns

## Overview
Production-ready patterns for Guidewire insurance platform integration. Guidewire exposes both REST (Cloud API) and SOAP (legacy PolicyCenter/ClaimCenter) endpoints. The Cloud API uses JSON over REST for modern integrations while legacy on-prem requires SOAP/XML with WS-Security. A structured client abstracts this hybrid, providing consistent error handling and typed responses across both surfaces.

## Singleton Client
```typescript
let _client: GuidewireClient | null = null;
export function getClient(): GuidewireClient {
  if (!_client) {
    const key = process.env.GUIDEWIRE_API_KEY, base = process.env.GUIDEWIRE_BASE_URL;
    if (!key || !base) throw new Error('GUIDEWIRE_API_KEY and GUIDEWIRE_BASE_URL must be set');
    _client = new GuidewireClient(base, key);
  }
  return _client;
}
class GuidewireClient {
  private h: Record<string, string>;
  constructor(private base: string, key: string) {
    this.h = { 'Authorization': `Bearer ${key}`, 'Content-Type': 'application/json' };
  }
  async getPolicies(filter?: string): Promise<GWPolicy[]> {
    const url = `${this.base}/pc/rest/common/v1/policies${filter ? `?filter=${encodeURIComponent(filter)}` : ''}`;
    const r = await fetch(url, { headers: this.h });
    if (!r.ok) throw new GWError(r.status, await r.text()); return (await r.json()).data;
  }
  async getClaims(policyId: string): Promise<GWClaim[]> {
    const r = await fetch(`${this.base}/cc/rest/common/v1/claims?policyId=${policyId}`, { headers: this.h });
    if (!r.ok) throw new GWError(r.status, await r.text()); return (await r.json()).data;
  }
  async createClaim(payload: Partial<GWClaim>): Promise<GWClaim> {
    const r = await fetch(`${this.base}/cc/rest/common/v1/claims`, {
      method: 'POST', headers: this.h, body: JSON.stringify({ data: { attributes: payload } }) });
    if (!r.ok) throw new GWError(r.status, await r.text()); return (await r.json()).data;
  }
}
```

## Error Wrapper
```typescript
export class GWError extends Error {
  constructor(public status: number, message: string) { super(message); this.name = 'GWError'; }
}
export async function safeCall<T>(op: string, fn: () => Promise<T>): Promise<T> {
  try { return await fn(); }
  catch (e: any) {
    if (e instanceof GWError && e.status === 429) { await new Promise(r => setTimeout(r, 5000)); return fn(); }
    if (e instanceof GWError && e.status === 401) throw new GWError(401, 'Invalid GUIDEWIRE_API_KEY');
    if (e instanceof GWError && e.status === 409) throw new GWError(409, `${op}: entity conflict`);
    throw new GWError(e.status ?? 0, `${op} failed: ${e.message}`);
  }
}
```

## Request Builder
```typescript
class GWQuery {
  private f: string[] = []; private inc: string[] = [];
  policyStatus(s: 'Draft' | 'Bound' | 'Cancelled') { this.f.push(`status eq '${s}'`); return this; }
  product(code: string) { this.f.push(`productCode eq '${code}'`); return this; }
  effectiveAfter(d: string) { this.f.push(`effectiveDate ge '${d}'`); return this; }
  include(...fields: string[]) { this.inc = fields; return this; }
  build() {
    const p = []; if (this.f.length) p.push(`filter=${this.f.join(' and ')}`);
    if (this.inc.length) p.push(`included=${this.inc.join(',')}`); return p.join('&');
  }
}
// Usage: new GWQuery().policyStatus('Bound').product('PersonalAuto').build();
```

## Response Types
```typescript
interface GWPolicy {
  id: string; policyNumber: string; productCode: string; status: 'Draft' | 'Bound' | 'Cancelled' | 'Expired';
  effectiveDate: string; expirationDate: string; insuredName: string; totalPremium: number;
}
interface GWClaim {
  id: string; claimNumber: string; policyId: string; lossDate: string;
  status: 'Open' | 'Closed' | 'Reopened'; lossType: string; totalIncurred: number;
}
interface GWActivity {
  id: string; subject: string; assignedTo: string; dueDate: string;
  priority: 'Low' | 'Normal' | 'High' | 'Urgent'; status: 'Open' | 'Completed' | 'Skipped';
}
```

## Testing Utilities
```typescript
export const mockPolicy = (o: Partial<GWPolicy> = {}): GWPolicy => ({ id: 'pc:1001',
  policyNumber: 'PA-2025-001', productCode: 'PersonalAuto', status: 'Bound',
  effectiveDate: '2025-01-01', expirationDate: '2026-01-01', insuredName: 'Jane Doe', totalPremium: 1200, ...o });
export const mockClaim = (o: Partial<GWClaim> = {}): GWClaim => ({ id: 'cc:2001',
  claimNumber: 'CLM-2025-001', policyId: 'pc:1001', lossDate: '2025-03-15',
  status: 'Open', lossType: 'Collision', totalIncurred: 5000, ...o });
```

## Error Handling
| Pattern | When to Use | Example |
|---------|-------------|---------|
| `safeCall` wrapper | All Cloud API calls | Structured error with operation context |
| Retry on 429 | Batch claim imports | 5s backoff before retry |
| Conflict detection | Concurrent policy edits | 409 returns clear merge-conflict message |
| SOAP fallback | Legacy on-prem endpoints | XML envelope with WS-Security header |

## Resources
- [Guidewire Developer Portal](https://developer.guidewire.com/)

## Next Steps
Apply patterns in `guidewire-core-workflow-a`.
