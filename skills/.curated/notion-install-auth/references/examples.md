# Full Setup Examples

Complete, copy-paste-ready client initialization for both official SDKs. Each
example configures the client with an explicit timeout and pinned API version,
verifies the connection with `users.me()`, then exercises a second call
(`users.list()`) so you can confirm the integration has real workspace access —
not just a valid token.

## TypeScript — Full Setup

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({
  auth: process.env.NOTION_TOKEN,
  timeoutMs: 60_000,
  notionVersion: '2022-06-28',
});

// Verify connection
const me = await notion.users.me({});
console.log(`Connected as ${me.name}`);

// List all users in the workspace
const users = await notion.users.list({});
console.log(`Workspace has ${users.results.length} users`);
```

Notes:

- `timeoutMs` caps each request; the SDK retries transient failures with
  exponential backoff automatically.
- Pinning `notionVersion` to `2022-06-28` keeps response shapes stable across
  SDK upgrades. Bump it deliberately, never implicitly.
- `users.list({})` requires the **Read user information** capability on the
  integration; without it the call returns `restricted_resource`.

## Python — Full Setup

```python
import os
from notion_client import Client

notion = Client(auth=os.environ["NOTION_TOKEN"])

# Verify connection
me = notion.users.me()
print(f"Connected as {me['name']} ({me['type']})")

# List all users in the workspace
users = notion.users.list()
print(f"Workspace has {len(users['results'])} users")
```

Notes:

- The Python SDK returns plain dicts, so index results with `me['name']` /
  `users['results']` rather than attribute access.
- Reading the token via `os.environ["NOTION_TOKEN"]` (bracket form) raises
  `KeyError` early if the variable is unset — a fast, obvious failure beats a
  silent `None` auth later.

## What success looks like

A working setup prints the bot user's name from `users.me()` and a non-zero
workspace user count from `users.list()`. If `users.me()` succeeds but a page
or database query returns `object_not_found`, the token is valid but the target
resource has not been shared with the integration — fix that in the page's
`...` → **Connections** menu, not in code.
