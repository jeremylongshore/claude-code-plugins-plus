# Examples

Worked examples for authenticating and verifying an `intercom-client` setup.

## Example 1: Access-Token Client (Private App)

The common path — a private app accessing your own workspace.

```typescript
import { IntercomClient } from "intercom-client";

const client = new IntercomClient({
  token: process.env.INTERCOM_ACCESS_TOKEN!,
});
```

Store the token securely:

```bash
# .env (add to .gitignore)
INTERCOM_ACCESS_TOKEN=dG9rOmFiY2RlZmdoaWprbG1ub3BxcnN0dXZ3eHl6

# Verify .gitignore includes .env
echo '.env' >> .gitignore
```

## Example 2: Verify the Connection

List admins to confirm the token works end-to-end:

```typescript
async function verifyConnection() {
  try {
    // List admins to verify the token works
    const admins = await client.admins.list();
    console.log("Connected! Admins:", admins.admins.length);
    for (const admin of admins.admins) {
      console.log(`  - ${admin.name} (${admin.email})`);
    }
  } catch (error) {
    if (error instanceof Error) {
      console.error("Connection failed:", error.message);
    }
  }
}

verifyConnection();
```

Expected output on success:

```
Connected! Admins: 3
  - Ada Lovelace (ada@example.com)
  - Grace Hopper (grace@example.com)
  - Alan Turing (alan@example.com)
```

## Example 3: OAuth Client (Public App)

See [oauth.md](oauth.md) for the full public-app OAuth exchange, then initialize
the client with the returned token:

```typescript
const client = new IntercomClient({ token: oauthToken });
```
