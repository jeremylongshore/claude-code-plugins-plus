# ClickHouse Local Dev Loop — Examples

Concrete, copy-pasteable examples for the everyday dev loop: bringing the
container up, seeding, querying, and inspecting server state.

## Example 1: Cold start to first query

```bash
# Bring the stack up and wait for readiness
docker compose up -d
curl http://localhost:8123/ping        # → "Ok.\n"

# Seed 1000 synthetic events
npm run db:seed                          # runs tsx scripts/seed.ts

# Confirm the rows landed
curl 'http://localhost:8123/?query=SELECT+count()+FROM+app.events'
# → 1000
```

## Example 2: Interactive SQL shell

```bash
# Open a clickhouse-client session inside the container
docker exec -it <container> clickhouse-client --password dev_password

# Or via the package script
npm run db:shell
```

```sql
-- Once inside the shell
SELECT event_type, count() AS n
FROM app.events
GROUP BY event_type
ORDER BY n DESC;
```

## Example 3: Run a query from the host over HTTP

```bash
# URL-encode the query and hit the HTTP interface
curl 'http://localhost:8123/?query=SELECT+event_type,count()+FROM+app.events+GROUP+BY+event_type+FORMAT+PrettyCompact'
```

## Example 4: Inspect server state

```bash
# Currently running queries
curl 'http://localhost:8123/?query=SELECT+*+FROM+system.processes+FORMAT+PrettyCompact'

# In-flight background merges
curl 'http://localhost:8123/?query=SELECT+*+FROM+system.merges+FORMAT+PrettyCompact'
```

## Example 5: Reset the environment between test runs

```bash
# Drop the volume and recreate a clean container + schema
npm run db:reset          # docker compose down -v && docker compose up -d
npm run db:seed           # re-seed fresh data
```

## Example 6: A passing integration test run

```bash
npm test
# ✓ tests/events.test.ts (1)
#   ✓ ClickHouse events (1)
#     ✓ inserts and queries events
```

The `beforeEach` hook in `tests/setup.ts` TRUNCATEs `app.events` before every
test, so each case starts from an empty table and the assertion
`expect(Number(row.cnt)).toBe(2)` is deterministic.
