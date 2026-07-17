# Notion Multi-Environment Setup — Examples

Full working examples that combine the factory, validation, and guard helpers
from [implementation.md](implementation.md).

## Full Initialization Pattern

Wire startup validation, the client factory, and a connectivity check into one
entry point your app calls on boot.

```typescript
import { Client } from '@notionhq/client';

// Initialize with full validation
async function initNotion(): Promise<{ client: Client; dbId: string }> {
  validateNotionConfig();
  const client = createNotionClient();
  const dbId = getDatabaseId('tasks');

  // Verify connectivity
  const me = await client.users.me({});
  console.log(`Connected as: ${me.name} (${me.type})`);

  // Verify database access
  const db = await client.databases.retrieve({ database_id: dbId });
  console.log(`Database: ${db.title[0]?.plain_text ?? 'Untitled'}`);

  return { client, dbId };
}
```

## Quick Environment Check Script

Run this before a deployment to confirm the injected token authenticates and
points at the intended workspace.

```bash
#!/bin/bash
# verify-notion-env.sh — run before deployment
echo "Environment: ${NODE_ENV:-development}"
echo "Token prefix: ${NOTION_TOKEN:0:8}..."

curl -sf https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" \
  | jq '{name: .name, type: .type, bot_owner: .bot.owner.type}' \
  || echo "ERROR: Cannot authenticate with Notion"
```
