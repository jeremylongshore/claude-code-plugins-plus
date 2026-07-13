# Error Handling Reference

## Database Trigger Errors

| Issue | Cause | Solution |
|-------|-------|----------|
| Trigger not firing | Trigger disabled or not attached | `ALTER TABLE orders ENABLE TRIGGER on_order_created;` and verify with `SELECT tgname, tgenabled FROM pg_trigger WHERE tgrelid = 'orders'::regclass;` |
| `pg_net` 404 response | Edge Function URL wrong or not deployed | Run `supabase functions deploy <name>`, check URL matches project ref |
| `pg_net` 401 response | Missing or invalid Authorization header | Set service role key via `ALTER DATABASE postgres SET app.settings.service_role_key = 'your-key';` |
| Trigger silently fails | `SECURITY DEFINER` without explicit `search_path` | Add `SET search_path = public, extensions;` to the function definition |
| `net._http_response` empty | Extension not enabled or wrong schema | `CREATE EXTENSION IF NOT EXISTS pg_net WITH SCHEMA extensions;` |
| Payload too large for NOTIFY | NOTIFY payload exceeds 8000 bytes | Send only record IDs, fetch full data in the listener |
| Duplicate trigger execution | Multiple triggers on same event | Review with `SELECT * FROM pg_trigger WHERE tgrelid = 'orders'::regclass;` |

## Edge Function Errors

| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature (401) | Webhook secret mismatch or encoding issue | Verify both sides use the same secret and UTF-8 encoding |
| Function timeout | Processing takes too long (default 60s) | Offload heavy work to a queue; return 200 immediately |
| Duplicate processing | No idempotency check | Add `processed_events` table with unique `event_id` constraint |
| JSON parse error | Malformed payload from trigger | Wrap `JSON.parse()` in try/catch, return 400 with details |
| CORS errors on Realtime | Browser blocks WebSocket | Ensure Supabase URL is correct; Realtime uses WSS, not HTTP |

## Realtime Subscription Errors

| Issue | Cause | Solution |
|-------|-------|----------|
| No events received | Table not in Realtime publication | Dashboard > Database > Replication > toggle table on |
| Subscription status `CHANNEL_ERROR` | RLS policy blocks the subscription | Ensure anon/authenticated role has SELECT on the table |
| Stale data after reconnect | Client missed events during disconnect | Re-fetch data on `SUBSCRIBED` status callback |
| Too many channels | Client opening channels without cleanup | Call `supabase.removeChannel(channel)` when unmounting |

## Debugging Commands

```sql
-- List all triggers on a table
SELECT tgname, tgenabled, tgtype, pg_get_triggerdef(oid)
FROM pg_trigger
WHERE tgrelid = 'public.orders'::regclass
AND NOT tgisinternal;

-- Check pg_net response log
SELECT id, status_code, content, created
FROM net._http_response
WHERE status_code >= 400
ORDER BY created DESC
LIMIT 20;

-- Verify pg_net extension is active
SELECT extname, extversion FROM pg_extension WHERE extname = 'pg_net';
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
