# Python Equivalents — Auth, Storage, Realtime

Extracted from SKILL.md. The TypeScript examples in the skill body are the
canonical flow; these are the `supabase-py` equivalents, section by section.

## Auth — registration, login, OAuth, session management

**Python**

```python
from supabase import create_client

supabase = create_client(
    "https://your-project.supabase.co",
    "your-anon-key"
)

# Sign up
result = supabase.auth.sign_up({
    "email": "user@example.com",
    "password": "secure-password-123",
    "options": {"data": {"username": "newuser"}},
})

# Sign in with password
result = supabase.auth.sign_in_with_password({
    "email": "user@example.com",
    "password": "secure-password-123",
})
access_token = result.session.access_token

# Get current session
session = supabase.auth.get_session()

# Sign out
supabase.auth.sign_out()
```

## Storage — upload, download, remove

**Python**

```python
# Upload
with open("report.pdf", "rb") as f:
    result = supabase.storage.from_("documents").upload(
        "user123/report.pdf", f,
        {"content-type": "application/pdf", "cache-control": "3600"}
    )

# Download
data = supabase.storage.from_("documents").download("user123/report.pdf")

# Public URL
url = supabase.storage.from_("avatars").get_public_url("user123/avatar.png")

# Signed URL (3600 seconds)
result = supabase.storage.from_("documents").create_signed_url(
    "user123/report.pdf", 3600
)
signed_url = result["signedURL"]

# List files
files = supabase.storage.from_("documents").list("user123")

# Delete
supabase.storage.from_("documents").remove(["user123/old-file.pdf"])
```

## Realtime — Postgres Changes subscription

**Python Realtime:**

```python
# Python realtime uses callbacks (requires running event loop)
def handle_insert(payload):
    print("New row:", payload["new"])

channel = supabase.channel("room")
channel.on_postgres_changes(
    event="INSERT",
    schema="public",
    table="messages",
    callback=handle_insert,
)
channel.subscribe()

# When done
supabase.remove_channel(channel)
```
