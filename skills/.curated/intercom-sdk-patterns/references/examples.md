# Intercom SDK — Worked Examples

End-to-end usage examples that combine the patterns from `SKILL.md` and
`references/implementation.md`.

## Cursor-Based Pagination (manual generator)

Intercom uses cursor-based pagination. The `starting_after` parameter points to
the next page. This generator streams every contact without holding the full
list in memory.

```typescript
// Generic paginator for any list endpoint
async function* paginateContacts(
  client: IntercomClient,
  perPage = 50
): AsyncGenerator<Intercom.Contact> {
  let startingAfter: string | undefined;

  do {
    const page = await client.contacts.list({
      perPage,
      startingAfter,
    });

    for (const contact of page.data) {
      yield contact;
    }

    // Cursor for next page
    startingAfter = page.pages?.next?.startingAfter ?? undefined;
  } while (startingAfter);
}

// Usage
const client = getClient();
for await (const contact of paginateContacts(client)) {
  console.log(contact.email);
}
```

The SDK also supports built-in iteration, which handles the cursor for you:

```typescript
// SDK auto-pagination (articles, contacts, etc.)
const response = await client.articles.list();
for await (const article of response) {
  console.log(article.title);
}
```

## Contact Search with Compound Queries

Combine multiple conditions with `AND` / `OR` operators, paginate the results,
and sort them. See `references/implementation.md` for the full operator table.

```typescript
// Search with multiple conditions (AND/OR)
const results = await client.contacts.search({
  query: {
    operator: "AND",
    value: [
      { field: "role", operator: "=", value: "user" },
      { field: "custom_attributes.plan", operator: "=", value: "pro" },
      {
        operator: "OR",
        value: [
          { field: "email", operator: "~", value: "@acme.com" },
          { field: "email", operator: "~", value: "@bigcorp.com" },
        ],
      },
    ],
  },
  pagination: { per_page: 25 },
  sort: { field: "created_at", order: "descending" },
});
```

## Resilient Call: Retry + Safe Wrapper Combined

Compose `withRetry` and `safeIntercomCall` so a single call gets both automatic
backoff on transient failures and normalized `{ data, error }` output.

```typescript
const { data: contact, error } = await safeIntercomCall(
  () => withRetry(() => client.contacts.find({ contactId: "abc123" })),
  "findContactResilient"
);

if (error) {
  // Non-recoverable after retries — inspect error.statusCode
} else {
  console.log(contact?.email);
}
```
