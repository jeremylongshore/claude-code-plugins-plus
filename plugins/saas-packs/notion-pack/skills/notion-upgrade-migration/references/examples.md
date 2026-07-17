# Worked Examples

Concrete recipes for common upgrade and migration follow-ons.

## Rollback After Failed Upgrade

```bash
# Revert to exact previous version
npm install @notionhq/client@2.2.14 --save-exact

# Restore any source changes
git checkout -- src/

# Verify rollback
npm test
npm ls @notionhq/client
```

## Adopting Comments API After Upgrade

```typescript
// Available since @notionhq/client 2.2.0
// Add a comment to a page
await notion.comments.create({
  parent: { page_id: pageId },
  rich_text: [{ text: { content: 'Automated review comment from CI' } }],
});

// List all comments on a page
const { results: comments } = await notion.comments.list({
  block_id: pageId,
});
for (const comment of comments) {
  const text = comment.rich_text.map(rt => rt.plain_text).join('');
  console.log(`${comment.created_by.id}: ${text}`);
}
```

## Detecting New Property Types in Existing Databases

```typescript
// After upgrade, scan databases for new property types your code may not handle
async function auditPropertyTypes(databaseId: string): Promise<void> {
  const db = await notion.databases.retrieve({ database_id: databaseId });
  const knownTypes = new Set([
    'title', 'rich_text', 'number', 'select', 'multi_select',
    'date', 'checkbox', 'url', 'email', 'phone_number',
    'formula', 'relation', 'rollup', 'people', 'files',
    'created_time', 'last_edited_time', 'created_by', 'last_edited_by',
    'status', 'unique_id',  // Newer types
  ]);

  for (const [name, prop] of Object.entries(db.properties)) {
    if (!knownTypes.has(prop.type)) {
      console.warn(`Unknown property type "${prop.type}" on "${name}" — add handler`);
    }
  }
}
```

## Deprecation Monitoring Script

```bash
#!/usr/bin/env bash
# Check for known deprecated patterns in your codebase.
# Notion introduced explicit API versioning with 2022-02-22; the client
# notionVersion option supersedes the raw Notion-Version request header.
set -euo pipefail
echo "=== Notion SDK Deprecation Audit ==="

# Check for deprecated header format
grep -rn "Notion-Version" --include="*.ts" --include="*.js" src/ 2>/dev/null && \
  echo "WARN: Raw Notion-Version header found — use client notionVersion option instead"

# Check for untyped page responses
grep -rn "as any" --include="*.ts" src/ 2>/dev/null | grep -i notion && \
  echo "WARN: Type assertions on Notion responses — use PageObjectResponse type"

# Check SDK version against latest
CURRENT=$(npm ls @notionhq/client --depth=0 2>/dev/null | grep @notionhq | sed 's/.*@//')
LATEST=$(npm view @notionhq/client version 2>/dev/null)
if [ "$CURRENT" != "$LATEST" ]; then
  echo "UPDATE: Running $CURRENT, latest is $LATEST"
else
  echo "OK: Running latest ($CURRENT)"
fi
```
