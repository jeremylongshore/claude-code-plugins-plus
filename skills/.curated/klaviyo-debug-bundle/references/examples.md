# Klaviyo Debug Bundle — Examples

## Example 1: Programmatic debug info (TypeScript)

When you want a structured object instead of a tarball — for example to surface
SDK version, connectivity, and API latency inside an app health check or a
support-tooling endpoint — collect the same signals via the SDK.

```typescript
// src/klaviyo/debug.ts
import { ApiKeySession, AccountsApi, ProfilesApi } from 'klaviyo-api';

interface KlaviyoDebugInfo {
  sdkVersion: string;
  apiConnected: boolean;
  accountId?: string;
  accountName?: string;
  apiLatencyMs: number;
  rateLimitStatus?: string;
  error?: string;
}

export async function collectKlaviyoDebugInfo(): Promise<KlaviyoDebugInfo> {
  const start = Date.now();
  const sdkVersion = require('klaviyo-api/package.json').version;

  try {
    const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
    const accountsApi = new AccountsApi(session);
    const result = await accountsApi.getAccounts();
    const account = result.body.data[0];

    return {
      sdkVersion,
      apiConnected: true,
      accountId: account.id,
      accountName: account.attributes.contactInformation?.organizationName,
      apiLatencyMs: Date.now() - start,
    };
  } catch (error: any) {
    return {
      sdkVersion,
      apiConnected: false,
      apiLatencyMs: Date.now() - start,
      error: `${error.status || 'N/A'}: ${error.body?.errors?.[0]?.detail || error.message}`,
    };
  }
}
```

## Example 2: Generate a bundle for a failing send

A campaign is not sending and Klaviyo support asks for diagnostics.

```bash
# From the application root so logs/ is discoverable
export KLAVIYO_PRIVATE_KEY="pk_your_private_key"
./klaviyo-debug-bundle.sh
# → Bundle created: klaviyo-debug-20241015-093214.tar.gz
```

Expected `summary.txt` when auth is healthy:

```
--- API Key Status ---
KLAVIYO_PRIVATE_KEY: SET (39 chars, prefix: pk_***)
--- API Connectivity ---
DNS resolve a.klaviyo.com: OK
API Auth Test: HTTP 200
Status Page: All Systems Operational
```

## Example 3: Reading the auth result

The `API Auth Test: HTTP NNN` line is the fastest triage signal:

| HTTP code | Meaning | Next action |
| --- | --- | --- |
| `200` | Key valid, API reachable | Auth is fine — look at logs / rate limits |
| `401` | Invalid or revoked key | Rotate `KLAVIYO_PRIVATE_KEY`, re-run |
| `403` | Key lacks scope for endpoint | Grant the scope in Klaviyo settings |
| `429` | Rate limited | See `klaviyo-rate-limits`; inspect `rate-limits.txt` |
| `000` | No response (DNS / network / TLS) | Check the DNS line and outbound firewall |
