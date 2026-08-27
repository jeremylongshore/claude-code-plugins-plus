# ClickHouse SDK Patterns — Worked Examples

Concrete, runnable usage of the patterns. Each example calls the helpers defined
in `SKILL.md` (typed query helper) and `references/implementation.md` (streaming,
batching, error handling).

## Example 1: Typed aggregation query

Call the generic `query<T>` helper with a typed row shape and named parameters.
ClickHouse returns numeric columns as strings in JSON, so type `cnt` as `string`.

```typescript
// Usage
interface EventCount {
  event_type: string;
  cnt: string;  // ClickHouse JSON returns numbers as strings
}

const rows = await query<EventCount>(
  'SELECT event_type, count() AS cnt FROM events WHERE user_id = {user_id:UInt64} GROUP BY event_type',
  { user_id: 42 }
);
```

## Example 2: Streaming a large result set

Iterate a multi-million-row `SELECT` without loading it all into memory, using
the `streamQuery` async generator from `references/implementation.md`.

```typescript
// Usage
for await (const event of streamQuery<{ event_type: string }>('SELECT * FROM events')) {
  process.stdout.write(`${event.event_type}\n`);
}
```

## Example 3: Safe query with structured error result

Wrap a query so callers get a discriminated `{ data, error }` result instead of a
thrown exception — see `safeQuery` in `references/implementation.md`.

```typescript
const { data, error } = await safeQuery<EventCount>(
  'SELECT event_type, count() AS cnt FROM events GROUP BY event_type'
);
if (error) {
  // error is a normalized string like "CH-60: ..." for server-side failures
  console.error(error);
} else {
  console.log(data);
}
```
