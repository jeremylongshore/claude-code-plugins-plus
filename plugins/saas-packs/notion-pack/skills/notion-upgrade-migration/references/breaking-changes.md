# Breaking Changes to Check After a Major Version Bump

Review these after any `@notionhq/client` or `notion-client` major version bump, before merging the upgrade branch.

## Node.js / TypeScript

```typescript
// 1. Import paths — endpoint types moved in some releases
// OLD (pre-2.2.x):
import type { QueryDatabaseResponse } from '@notionhq/client/build/src/api-endpoints';
// CURRENT (2.2.x):
import type {
  PageObjectResponse,
  DatabaseObjectResponse,
  BlockObjectResponse,
  QueryDatabaseResponse,
} from '@notionhq/client/build/src/api-endpoints';

// 2. Error handling imports are stable across all 2.x versions
import { Client, isNotionClientError, APIErrorCode, ClientErrorCode } from '@notionhq/client';

// 3. New property types — code must handle unknown types gracefully
function extractProperty(prop: any): string {
  switch (prop.type) {
    case 'title': return prop.title.map((t: any) => t.plain_text).join('');
    case 'rich_text': return prop.rich_text.map((t: any) => t.plain_text).join('');
    case 'status': return prop.status?.name ?? '';       // Added in 2.2.3
    case 'unique_id': return String(prop.unique_id?.number ?? ''); // Added in 2.2.4
    default: return `[unhandled: ${prop.type}]`;
  }
}

// 4. Pin API version explicitly for reproducible behavior
const notion = new Client({
  auth: process.env.NOTION_TOKEN,
  notionVersion: '2022-06-28',  // Always pin — do not rely on SDK default
});
```

## Python

```python
from notion_client import Client, APIResponseError

# Pin API version explicitly
notion = Client(
    auth=os.environ["NOTION_TOKEN"],
    notion_version="2022-06-28",  # Explicit pin
)

# New in recent versions: comments API
comments = notion.comments.list(block_id=page_id)

# Status property (requires SDK that supports it)
# Returns: {"type": "status", "status": {"name": "In Progress", "color": "blue"}}
```
