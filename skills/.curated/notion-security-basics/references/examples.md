# Worked Examples

End-to-end examples for a dual-integration (reader/writer) architecture and a
startup validation script that fails fast on missing or invalid configuration.

## Full `.env` Setup for Dual Integration Architecture

```bash
# .env — never committed
# Reader integration (Read content only)
NOTION_READ_TOKEN=ntn_reader_integration_token

# Writer integration (Read + Update + Insert)
NOTION_WRITE_TOKEN=ntn_writer_integration_token

# OAuth2 (public integration only)
NOTION_OAUTH_CLIENT_ID=abc123
NOTION_OAUTH_CLIENT_SECRET=secret_abc123
NOTION_OAUTH_REDIRECT_URI=https://app.example.com/auth/notion/callback

# Target resources
NOTION_DATABASE_ID=your_database_id
```

## Startup Validation Script

```typescript
// validate-notion-config.ts — run at application startup
import { Client } from '@notionhq/client';

async function validateNotionConfig(): Promise<void> {
  const requiredVars = ['NOTION_READ_TOKEN', 'NOTION_DATABASE_ID'];
  const missing = requiredVars.filter((v) => !process.env[v]);

  if (missing.length > 0) {
    throw new Error(`Missing required env vars: ${missing.join(', ')}`);
  }

  const notion = new Client({ auth: process.env.NOTION_READ_TOKEN });

  // Verify token is valid
  try {
    const me = await notion.users.me({});
    console.log(`Notion auth OK: bot "${me.name}" (${me.id})`);
  } catch (error: any) {
    if (error.code === 'unauthorized') {
      throw new Error('NOTION_READ_TOKEN is invalid or expired — rotate at notion.so/my-integrations');
    }
    throw error;
  }

  // Verify database is accessible
  try {
    await notion.databases.retrieve({
      database_id: process.env.NOTION_DATABASE_ID!,
    });
    console.log('Notion database access OK');
  } catch (error: any) {
    if (error.code === 'object_not_found') {
      throw new Error(
        'NOTION_DATABASE_ID not found — ensure the database is shared with the integration'
      );
    }
    throw error;
  }
}

validateNotionConfig().catch((err) => {
  console.error('Notion configuration validation failed:', err.message);
  process.exit(1);
});
```
