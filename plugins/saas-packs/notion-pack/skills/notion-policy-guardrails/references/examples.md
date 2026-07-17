# Notion Policy & Guardrails — Examples

Ready-to-use snippets for common governance checks. See `references/implementation.md`
for the full enforcement functions these build on.

## Quick Compliance Check

```bash
# One-line secret scan for CI
grep -rn "ntn_\|secret_" --include="*.ts" --include="*.js" src/ && echo "FAIL: Token found" || echo "PASS: No tokens"

# Check .env files not committed
git ls-files | grep -E "^\.env" && echo "FAIL: .env committed" || echo "PASS"
```

## Schema Registry

Define the expected schema for each governed database once, then feed it to
`validateSchemaInCI` (see `references/implementation.md`) so CI fails when a
property is renamed or retyped in the Notion UI.

```typescript
// Define expected schemas for CI validation
const SCHEMA_REGISTRY = {
  tasks: {
    database_id: process.env.NOTION_TASKS_DB!,
    requiredProperties: {
      'Name': 'title',
      'Status': 'select',
      'Assignee': 'people',
      'Due Date': 'date',
      'Priority': 'select',
    },
  },
  content: {
    database_id: process.env.NOTION_CONTENT_DB!,
    requiredProperties: {
      'Title': 'title',
      'Status': 'select',
      'Published Date': 'date',
      'Author': 'people',
      'Tags': 'multi_select',
    },
  },
};
```
