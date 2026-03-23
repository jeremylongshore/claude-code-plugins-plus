# Examples

## Testing Webhooks Locally

### 1. Start Supabase Locally

```bash
supabase start
# Note the API URL and service_role key from output
```

### 2. Expose Local Edge Function with ngrok

```bash
# Serve the Edge Function locally
supabase functions serve on-order-created --env-file .env.local

# In another terminal, expose it
ngrok http 54321
# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
```

### 3. Create the Trigger Pointing to ngrok

```sql
-- In local psql or Supabase SQL editor
CREATE OR REPLACE FUNCTION public.test_webhook()
RETURNS trigger AS $$
BEGIN
  PERFORM net.http_post(
    url     := 'https://abc123.ngrok.io/functions/v1/on-order-created',
    headers := '{"Content-Type": "application/json"}'::jsonb,
    body    := jsonb_build_object('type', TG_OP, 'record', row_to_json(NEW)::jsonb)
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER test_webhook_trigger
  AFTER INSERT ON public.orders
  FOR EACH ROW EXECUTE FUNCTION public.test_webhook();
```

### 4. Trigger the Event

```bash
# Insert a row to fire the webhook
curl -X POST 'http://localhost:54321/rest/v1/orders' \
  -H "apikey: <anon-key>" \
  -H "Authorization: Bearer <anon-key>" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2, "status": "pending"}'
```

### 5. Verify in ngrok Dashboard

Open `http://localhost:4040` to see the webhook request in ngrok's inspector.

## Manual Webhook Testing with curl

```bash
# Simulate an INSERT webhook payload
curl -X POST http://localhost:54321/functions/v1/on-order-created \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <service-role-key>" \
  -d '{
    "type": "INSERT",
    "table": "orders",
    "schema": "public",
    "record": {"id": 42, "product_id": 1, "quantity": 2, "status": "pending"},
    "old_record": null
  }'

# Simulate an UPDATE webhook payload
curl -X POST http://localhost:54321/functions/v1/on-order-created \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <service-role-key>" \
  -d '{
    "type": "UPDATE",
    "table": "orders",
    "schema": "public",
    "record": {"id": 42, "product_id": 1, "quantity": 2, "status": "shipped"},
    "old_record": {"id": 42, "product_id": 1, "quantity": 2, "status": "pending"}
  }'
```

## Realtime Subscription Test (Browser Console)

```javascript
// Paste in browser console with Supabase JS loaded
const { createClient } = supabase;
const client = createClient(
  "http://localhost:54321",
  "<anon-key>"
);

client
  .channel("test")
  .on("postgres_changes", { event: "*", schema: "public", table: "orders" },
    (payload) => console.log("Realtime event:", payload)
  )
  .subscribe((status) => console.log("Status:", status));

// Now insert a row via curl or the dashboard — you should see the event logged
```

## Auth Hook Test (Custom JWT Claims)

```sql
-- Create a user role mapping
INSERT INTO public.user_roles (user_id, role) VALUES
  ('<user-uuid>', 'admin');

-- Create the custom claims hook
CREATE OR REPLACE FUNCTION public.custom_access_token_hook(event jsonb)
RETURNS jsonb AS $$
DECLARE
  user_role text;
BEGIN
  SELECT role INTO user_role
  FROM public.user_roles
  WHERE user_id = (event->>'user_id')::uuid;

  event := jsonb_set(event, '{claims,user_role}', to_jsonb(COALESCE(user_role, 'user')));
  RETURN event;
END;
$$ LANGUAGE plpgsql STABLE;

-- Enable in Dashboard > Auth > Hooks > Custom Access Token
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
