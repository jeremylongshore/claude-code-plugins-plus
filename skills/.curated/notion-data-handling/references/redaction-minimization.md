# Redaction and Data Minimization

Two complementary controls: **redact** PII out of anything you log or export, and
**minimize** the data you pull from the API in the first place with `filter_properties`.

## Redact PII before logging or exporting

```typescript
function redactPageProperties(
  page: PageObjectResponse,
  sensitiveFields: string[] = ['Email', 'Phone', 'SSN']
): Record<string, unknown> {
  const redacted: Record<string, unknown> = { id: page.id };

  for (const [name, prop] of Object.entries(page.properties)) {
    // Always redact known sensitive property types
    if (prop.type === 'email') {
      redacted[name] = prop.email ? '[REDACTED_EMAIL]' : null;
      continue;
    }
    if (prop.type === 'phone_number') {
      redacted[name] = prop.phone_number ? '[REDACTED_PHONE]' : null;
      continue;
    }
    if (prop.type === 'people') {
      redacted[name] = `[${prop.people.length} users]`;
      continue;
    }

    // Redact explicitly marked sensitive fields
    if (sensitiveFields.includes(name)) {
      redacted[name] = '[REDACTED]';
      continue;
    }

    // Safe property types pass through
    switch (prop.type) {
      case 'title':
        redacted[name] = prop.title.map(t => t.plain_text).join('');
        break;
      case 'select':
        redacted[name] = prop.select?.name ?? null;
        break;
      case 'multi_select':
        redacted[name] = prop.multi_select.map(s => s.name);
        break;
      case 'number':
        redacted[name] = prop.number;
        break;
      case 'checkbox':
        redacted[name] = prop.checkbox;
        break;
      case 'date':
        redacted[name] = prop.date?.start ?? null;
        break;
      default:
        redacted[name] = `[${prop.type}]`;
    }
  }

  return redacted;
}

// Safe logging — never log raw page objects
console.log('Processing page:', JSON.stringify(redactPageProperties(page)));
// NEVER: console.log('Page:', JSON.stringify(page)); // LEAKS PII
```

The redactor is allowlist-shaped: known-sensitive property types (`email`, `phone_number`,
`people`) are always masked, explicitly-named `sensitiveFields` are masked, and only a
vetted set of safe scalar types passes through. Anything unrecognized collapses to a
`[type]` placeholder rather than leaking its value.

## Data minimization — only request the properties you need

```typescript
// filter_properties limits which properties are returned by the API
async function getTaskStatuses(dbId: string) {
  const response = await notion.databases.query({
    database_id: dbId,
    filter_properties: ['Status', 'Name', 'Due Date'],
    page_size: 100,
  });
  // Response only contains Status, Name, Due Date — no email, phone, etc.
  return response;
}
```

`filter_properties` accepts an array of property IDs/names and drops everything else from
the response payload. Pulling only the fields a task needs is the cheapest privacy control
available: PII that never enters your process cannot be logged, cached, or leaked.
