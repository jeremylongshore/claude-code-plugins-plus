# Notion Debug Bundle — Full Implementation

This reference carries the complete diagnostic scripts. `SKILL.md` shows the
lean Step 1 connectivity check inline; the full bundle collector and the
programmatic TypeScript diagnostics live here.

## Full Debug Bundle Script

Collects every diagnostic artifact into a single redacted tarball suitable for
attaching to a Notion support ticket.

```bash
#!/bin/bash
# notion-debug-bundle.sh — collects all diagnostic artifacts into a tarball
BUNDLE="notion-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE"

# --- Environment snapshot ---
cat > "$BUNDLE/environment.txt" << EOF
Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Node: $(node --version 2>/dev/null || echo "not found")
npm: $(npm --version 2>/dev/null || echo "not found")
SDK: $(npm ls @notionhq/client 2>/dev/null | grep notionhq || echo "not found")
NOTION_TOKEN: ${NOTION_TOKEN:+SET (prefix: ${NOTION_TOKEN:0:4})}
OS: $(uname -a)
EOF

# --- API auth response (avatar redacted) ---
# Notion-Version 2022-06-28 is the current stable REST API version.
curl -s https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" \
  | jq 'del(.avatar_url)' > "$BUNDLE/api-auth.json" 2>/dev/null

# --- Database access test (if DATABASE_ID is set) ---
if [ -n "$NOTION_DATABASE_ID" ]; then
  curl -s "https://api.notion.com/v1/databases/${NOTION_DATABASE_ID}" \
    -H "Authorization: Bearer ${NOTION_TOKEN}" \
    -H "Notion-Version: 2022-06-28" \
    | jq '{id, title: .title[0].plain_text, is_inline, created_time, last_edited_time}' \
    > "$BUNDLE/database-access.json" 2>/dev/null
else
  echo "NOTION_DATABASE_ID not set — skipping database access test" > "$BUNDLE/database-access.json"
fi

# --- Platform status with active incidents ---
curl -s https://status.notion.so/api/v2/summary.json \
  | jq '{status: .status, incidents: [.incidents[] | {name, status, updated_at}]}' \
  > "$BUNDLE/platform-status.json" 2>/dev/null

# --- Application logs (redacted) ---
for LOG_FILE in app.log server.log output.log; do
  if [ -f "$LOG_FILE" ]; then
    grep -i "notion\|notionhq\|api\.notion" "$LOG_FILE" | tail -100 \
      | sed 's/ntn_[a-zA-Z0-9_]*/ntn_[REDACTED]/g' \
      | sed 's/secret_[a-zA-Z0-9_]*/secret_[REDACTED]/g' \
      > "$BUNDLE/logs-${LOG_FILE%.log}-redacted.txt"
  fi
done

# --- Dependency tree for notion packages ---
npm ls @notionhq/client --all 2>/dev/null > "$BUNDLE/dependency-tree.txt"

# --- .env redacted copy ---
if [ -f ".env" ]; then
  sed 's/=.*/=[REDACTED]/' .env > "$BUNDLE/env-redacted.txt"
fi

# --- Package and clean up ---
tar -czf "$BUNDLE.tar.gz" "$BUNDLE"
rm -rf "$BUNDLE"
echo "Bundle created: $BUNDLE.tar.gz"
```

## Programmatic Diagnostics

Use the SDK directly when you want structured diagnostics inside a Node/TypeScript
app instead of the shell bundle. Tests auth, database access, and workspace-level
search, returning a plain object you can log or serialize.

```typescript
import { Client, isNotionClientError, APIErrorCode } from '@notionhq/client';

async function collectNotionDiagnostics(databaseId?: string) {
  const notion = new Client({ auth: process.env.NOTION_TOKEN });
  const debug: Record<string, unknown> = {
    timestamp: new Date().toISOString(),
    sdk: '@notionhq/client',
    nodeVersion: process.version,
    tokenSet: !!process.env.NOTION_TOKEN,
    tokenPrefix: process.env.NOTION_TOKEN?.substring(0, 4) ?? 'unset',
  };

  // Test authentication — /v1/users/me
  try {
    const me = await notion.users.me({});
    debug.auth = { status: 'ok', botName: me.name, type: me.type };
  } catch (error) {
    if (isNotionClientError(error)) {
      debug.auth = { status: 'error', code: error.code, message: error.message };
    }
  }

  // Test database access (if ID provided)
  if (databaseId) {
    try {
      const db = await notion.databases.retrieve({ database_id: databaseId });
      debug.database = {
        status: 'ok',
        title: (db as any).title?.[0]?.plain_text ?? 'untitled',
        isInline: (db as any).is_inline,
      };
    } catch (error) {
      if (isNotionClientError(error)) {
        debug.database = { status: 'error', code: error.code, message: error.message };
        if (error.code === APIErrorCode.ObjectNotFound) {
          debug.database.hint = 'Integration may not be invited to this database — share it via the page menu';
        }
      }
    }
  }

  // Test search (verifies workspace-level access)
  try {
    const search = await notion.search({ page_size: 1 });
    debug.search = {
      status: 'ok',
      accessiblePages: search.results.length > 0,
      resultType: search.results[0]?.object ?? 'none',
    };
  } catch (error) {
    if (isNotionClientError(error)) {
      debug.search = { status: 'error', code: error.code };
    }
  }

  return debug;
}
```
