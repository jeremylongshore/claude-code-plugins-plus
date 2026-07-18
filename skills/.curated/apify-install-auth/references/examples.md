# Apify Install & Auth — Worked Examples

Copy-paste-ready setups that go one step past the SKILL.md skeleton. Each is a
complete file you can drop into a real project.

## TypeScript Project Setup — Singleton Client

A lazily-initialized singleton so the whole app shares one authenticated client
and fails fast with a clear message when the token is missing.

```typescript
// src/apify/client.ts
import { ApifyClient } from 'apify-client';
import 'dotenv/config'; // npm install dotenv

let client: ApifyClient | null = null;

export function getClient(): ApifyClient {
  if (!client) {
    if (!process.env.APIFY_TOKEN) {
      throw new Error('APIFY_TOKEN environment variable is required');
    }
    client = new ApifyClient({ token: process.env.APIFY_TOKEN });
  }
  return client;
}
```

## .env.example Template

Commit this (with a placeholder), never the real `.env`.

```bash
# Apify — get your token at https://console.apify.com/account/integrations
APIFY_TOKEN=apify_api_REPLACE_ME
```

## Verify Connection Snippet

Confirm the token authenticates before wiring the client into the rest of the app.

```typescript
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({
  token: process.env.APIFY_TOKEN,
});

// List your Actors to confirm auth works
const { items } = await client.actors().list();
console.log(`Authenticated. You have ${items.length} Actors.`);
```

## CLI Verification

For interactive development where the CLI is installed globally.

```bash
apify login --token YOUR_TOKEN
apify info  # Shows your account info
```
