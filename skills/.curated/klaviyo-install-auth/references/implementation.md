# Klaviyo Install & Auth — Full Implementation Walkthrough

This is the complete, step-by-step implementation referenced from the lean
`SKILL.md`. It preserves every code block and edge-case detail so you can drill
in when you need depth beyond the high-level skeleton.

## Step 1: Install the Official SDK

```bash
# Node.js (official SDK -- NOT @klaviyo/sdk, that's deprecated)
npm install klaviyo-api

# Python
pip install klaviyo-api
```

> **Important:** The npm package is `klaviyo-api`, not `@klaviyo/sdk`. The SDK exports per-resource API classes (ProfilesApi, EventsApi, etc.) that each take an `ApiKeySession`.

## Step 2: Configure Authentication

```bash
# .env (NEVER commit to git)
KLAVIYO_PRIVATE_KEY=pk_***********************************
KLAVIYO_PUBLIC_KEY=UXxxXx    # Only for client-side endpoints

# .gitignore -- ensure secrets are excluded
echo '.env' >> .gitignore
echo '.env.local' >> .gitignore
```

Klaviyo uses two key types:

| Key Type | Prefix | Use Case | Header |
|----------|--------|----------|--------|
| Private API Key | `pk_` | Server-side REST API | `Authorization: Klaviyo-API-Key pk_***` |
| Public API Key | 6-char | Client-side Track/Identify | Query param `company_id` |

## Step 3: Initialize the SDK

```typescript
// src/klaviyo/client.ts
import { ApiKeySession, ProfilesApi, EventsApi, ListsApi } from 'klaviyo-api';

// Create a session with your private API key
const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);

// Instantiate per-resource API clients
export const profilesApi = new ProfilesApi(session);
export const eventsApi = new EventsApi(session);
export const listsApi = new ListsApi(session);
```

## Step 4: Verify Connection

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
    console.log(`Account ID: ${account.id}`);
  } catch (error: any) {
    if (error.status === 401) {
      console.error('Invalid API key. Check KLAVIYO_PRIVATE_KEY in your .env file.');
    } else if (error.status === 403) {
      console.error('API key lacks required scopes. Generate a new key with full access.');
    } else {
      console.error(`Connection failed: ${error.status} ${error.message}`);
    }
    process.exit(1);
  }
}

verifyKlaviyoConnection();
```

## Step 5: Set API Revision Header

All Klaviyo API requests require a `revision` header. The SDK handles this automatically, but if using raw HTTP:

```bash
# Direct cURL test
curl -X GET "https://a.klaviyo.com/api/profiles/" \
  -H "Authorization: Klaviyo-API-Key pk_***" \
  -H "revision: 2024-10-15" \
  -H "Accept: application/vnd.api+json"
```

## Python Setup

```python
# pip install klaviyo-api
from klaviyo_api import KlaviyoAPI

klaviyo = KlaviyoAPI(
    api_key="pk_***",
    max_delay=60,   # Max retry delay in seconds
    max_retries=3   # Number of retries on 429/5xx
)

# Verify connection
accounts = klaviyo.Accounts.get_accounts()
print(f"Connected: {accounts['data'][0]['attributes']['contact_information']['organization_name']}")
```

## API Scopes Reference

Generate keys with only the scopes your integration needs (least privilege):

| Scope | Required For |
|-------|-------------|
| `profiles:read` / `profiles:write` | Create/read/update profiles |
| `events:read` / `events:write` | Track events, query metrics |
| `lists:read` / `lists:write` | Manage lists, subscribe profiles |
| `segments:read` | Query segments and members |
| `campaigns:read` / `campaigns:write` | Create and send campaigns |
| `flows:read` / `flows:write` | Manage flow actions |
| `templates:read` / `templates:write` | Create/edit email templates |
| `data-privacy:write` | GDPR/CCPA deletion requests |
