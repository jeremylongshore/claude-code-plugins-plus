# Examples

Runnable smoke tests for both official SDKs, plus a pytest mocking example for Python.

## TypeScript: Quick Connection Test

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });

async function smokeTest() {
  const { results } = await notion.users.list({});
  console.log(`Connected. ${results.length} user(s) in workspace.`);

  // Verify dev database access
  const db = await notion.databases.retrieve({
    database_id: process.env.NOTION_TEST_DATABASE_ID!,
  });
  console.log(`Dev database: "${(db as any).title?.[0]?.plain_text || db.id}"`);
}

smokeTest().catch(console.error);
```

## Python: Dev Environment with notion-client

```python
import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv(".env.development")

notion = Client(auth=os.environ["NOTION_TOKEN"])

# Quick smoke test
users = notion.users.list()
print(f"Connected. {len(users['results'])} user(s) in workspace.")

# Query dev database
db_id = os.environ["NOTION_TEST_DATABASE_ID"]
results = notion.databases.query(database_id=db_id, page_size=1)
print(f"Dev database has {len(results['results'])} page(s) (showing 1)")

# Mock example for pytest
def test_query_with_mock(mocker):
    mock_notion = mocker.patch("notion_client.Client")
    mock_notion.return_value.databases.query.return_value = {
        "results": [{"id": "page-1"}],
        "has_more": False,
        "next_cursor": None,
    }
    client = Client(auth="ntn_test")
    result = client.databases.query(database_id="test-db")
    assert len(result["results"]) == 1
```
