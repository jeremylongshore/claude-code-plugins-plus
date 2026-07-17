# Reading Configuration from Notion in CI

Use a Notion database as a lightweight feature-flag or config store that non-engineers
can edit. The script queries the config database filtered by environment, extracts
`Key`/`Value` pairs, and writes `notion-config.json` for downstream CI steps to consume.

```typescript
// scripts/notion-read-config.js
import { Client } from '@notionhq/client';
import { writeFileSync } from 'fs';

const notion = new Client({ auth: process.env.NOTION_TOKEN });
const configDbId = process.env.NOTION_CONFIG_DB;

async function readConfig() {
  const response = await notion.databases.query({
    database_id: configDbId,
    filter: {
      property: 'Environment',
      select: { equals: process.env.DEPLOY_ENV || 'production' },
    },
  });

  const config = {};
  for (const page of response.results) {
    if (page.object !== 'page' || !('properties' in page)) continue;
    const props = page.properties;

    const keyProp = props['Key'];
    const valueProp = props['Value'];
    if (keyProp?.type !== 'title' || valueProp?.type !== 'rich_text') continue;

    const key = keyProp.title.map((t) => t.plain_text).join('');
    const value = valueProp.rich_text.map((t) => t.plain_text).join('');

    if (key) config[key] = value;
  }

  // Write config to file for downstream CI steps
  writeFileSync('notion-config.json', JSON.stringify(config, null, 2));
  console.log(`Loaded ${Object.keys(config).length} config entries from Notion`);
}

readConfig().catch((err) => {
  console.error('Failed to read config:', err.message);
  process.exit(1);
});
```

GitHub Actions step to consume:

```yaml
- name: Load feature flags from Notion
  run: node scripts/notion-read-config.js
  env:
    NOTION_TOKEN: ${{ secrets.NOTION_TOKEN }}
    NOTION_CONFIG_DB: ${{ secrets.NOTION_CONFIG_DB }}
    DEPLOY_ENV: production

- name: Use config in build
  run: |
    CONFIG=$(cat notion-config.json)
    echo "Feature flags loaded: $(echo $CONFIG | jq 'keys | length') entries"
```
