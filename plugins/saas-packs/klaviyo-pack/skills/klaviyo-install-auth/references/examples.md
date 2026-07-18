# Klaviyo Install & Auth — Worked Examples

Concrete end-to-end examples that build on the client configured in the main
walkthrough (`references/implementation.md`). Each one is a self-contained
sequence you can copy into a fresh project.

## Example 1: Fresh Node.js project from zero

```bash
# Install the official SDK
npm install klaviyo-api

# Store the private key (never commit it)
echo 'KLAVIYO_PRIVATE_KEY=pk_***********************************' >> .env
echo '.env' >> .gitignore
```

```typescript
// src/klaviyo/client.ts
import { ApiKeySession, ProfilesApi, EventsApi, ListsApi } from 'klaviyo-api';

const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);

export const profilesApi = new ProfilesApi(session);
export const eventsApi = new EventsApi(session);
export const listsApi = new ListsApi(session);
```

## Example 2: Verify the key works before deploying

Run the verification script once in CI or locally; it exits non-zero on a bad
key so a broken credential fails the build instead of surfacing at runtime.

```typescript
// src/klaviyo/verify.ts
import { ApiKeySession, AccountsApi } from 'klaviyo-api';

async function verifyKlaviyoConnection(): Promise<void> {
  const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
  const accountsApi = new AccountsApi(session);

  try {
    const accounts = await accountsApi.getAccounts();
    const account = accounts.body.data[0];
    console.log(`Connected to Klaviyo account: ${account.attributes.contactInformation.organizationName}`);
  } catch (error: any) {
    if (error.status === 401) {
      console.error('Invalid API key. Check KLAVIYO_PRIVATE_KEY in your .env file.');
    }
    process.exit(1);
  }
}

verifyKlaviyoConnection();
```

Expected output on success:

```text
Connected to Klaviyo account: Acme Coffee Co.
```

## Example 3: Python equivalent with retry tuning

```python
# pip install klaviyo-api
from klaviyo_api import KlaviyoAPI

klaviyo = KlaviyoAPI(
    api_key="pk_***",
    max_delay=60,   # Max retry delay in seconds
    max_retries=3   # Auto-retry on 429/5xx
)

accounts = klaviyo.Accounts.get_accounts()
print(f"Connected: {accounts['data'][0]['attributes']['contact_information']['organization_name']}")
```

## Example 4: Quick raw-HTTP smoke test (no SDK)

Useful for confirming a key from a shell before wiring any code:

```bash
curl -X GET "https://a.klaviyo.com/api/profiles/" \
  -H "Authorization: Klaviyo-API-Key pk_***" \
  -H "revision: 2024-10-15" \
  -H "Accept: application/vnd.api+json"
```

A `200` with a JSON `data` array confirms the key and revision header are valid;
a `401` means the key is wrong, a `403` means it is missing the `profiles:read`
scope.
