# Database Webhooks with `pg_net` and Trigger Functions

Database webhooks fire HTTP requests when rows change. Under the hood, Supabase uses the `pg_net` extension to make async, non-blocking HTTP calls from within PostgreSQL.

## Enable pg_net and Create the Trigger Function

```sql
-- Enable the pg_net extension (one-time)
CREATE EXTENSION IF NOT EXISTS pg_net WITH SCHEMA extensions;

-- Trigger function: POST to an Edge Function on every new order
CREATE OR REPLACE FUNCTION public.notify_order_created()
RETURNS trigger AS $$
BEGIN
  PERFORM net.http_post(
    url    := 'https://<project-ref>.supabase.co/functions/v1/on-order-created',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'Authorization', 'Bearer ' || current_setting('app.settings.service_role_key', true)
    ),
    body   := jsonb_build_object(
      'table',  TG_TABLE_NAME,
      'type',   TG_OP,
      'record', row_to_json(NEW)::jsonb,
      'old_record', CASE WHEN TG_OP = 'UPDATE' THEN row_to_json(OLD)::jsonb ELSE NULL END
    )
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

## Attach Triggers for INSERT, UPDATE, DELETE

```sql
-- Fire on new rows
CREATE TRIGGER on_order_created
  AFTER INSERT ON public.orders
  FOR EACH ROW EXECUTE FUNCTION public.notify_order_created();

-- Fire on status changes only (conditional trigger)
CREATE OR REPLACE FUNCTION public.notify_order_status_changed()
RETURNS trigger AS $$
BEGIN
  IF OLD.status IS DISTINCT FROM NEW.status THEN
    PERFORM net.http_post(
      url    := 'https://<project-ref>.supabase.co/functions/v1/on-status-change',
      headers := '{"Content-Type": "application/json"}'::jsonb,
      body   := jsonb_build_object(
        'order_id',   NEW.id,
        'old_status', OLD.status,
        'new_status', NEW.status,
        'changed_at', now()
      )
    );
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_order_status_changed
  AFTER UPDATE ON public.orders
  FOR EACH ROW EXECUTE FUNCTION public.notify_order_status_changed();
```

## Using `supabase_functions.http_request()` (Built-in Helper)

Supabase provides a built-in wrapper that simplifies calling Edge Functions from triggers without managing headers manually:

```sql
-- This is the function Supabase auto-creates for Dashboard-configured webhooks
-- You can also call it directly in your own trigger functions
CREATE TRIGGER on_profile_updated
  AFTER UPDATE ON public.profiles
  FOR EACH ROW
  EXECUTE FUNCTION supabase_functions.http_request(
    'https://<project-ref>.supabase.co/functions/v1/on-profile-update',
    'POST',
    '{"Content-Type": "application/json"}',
    '{}',  -- params
    '5000' -- timeout ms
  );
```

## Inspect pg_net Responses

```sql
-- Check recent HTTP responses (retained for 6 hours)
SELECT id, status_code, content, created
FROM net._http_response
ORDER BY created DESC
LIMIT 10;

-- Find failed requests
SELECT id, status_code, content
FROM net._http_response
WHERE status_code >= 400
ORDER BY created DESC;
```
