# Notion Core Workflow A — Examples & Helpers

Reusable helpers that sit alongside the core workflow. SKILL.md links here so
the main file stays focused on the workflow itself.

## Extract Property Values Helper

Reading a queried page's properties back into plain JavaScript values requires
switching on the property `type`, because every Notion property returns a
differently-shaped object. This helper normalizes the common types:

```typescript
function getPropertyValue(property: any): string | number | boolean | null {
  switch (property.type) {
    case 'title':
      return property.title.map((t: any) => t.plain_text).join('');
    case 'rich_text':
      return property.rich_text.map((t: any) => t.plain_text).join('');
    case 'number':
      return property.number;
    case 'select':
      return property.select?.name ?? null;
    case 'multi_select':
      return property.multi_select.map((s: any) => s.name).join(', ');
    case 'date':
      return property.date?.start ?? null;
    case 'checkbox':
      return property.checkbox;
    case 'url':
      return property.url;
    case 'email':
      return property.email;
    case 'formula':
      return property.formula?.[property.formula.type] ?? null;
    default:
      return null;
  }
}
```

Combine it with the pagination helper from
[the full walkthrough](implementation.md) (Step 6) to flatten an entire
database into an array of plain objects:

```typescript
const pages = await getAllPages(databaseId);
const rows = pages.map((page: any) => {
  const row: Record<string, unknown> = {};
  for (const [name, prop] of Object.entries(page.properties)) {
    row[name] = getPropertyValue(prop);
  }
  return row;
});
```
