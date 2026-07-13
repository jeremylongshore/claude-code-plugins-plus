# shopify.app.toml Configuration

Central app configuration file for Shopify CLI projects. Includes scopes, auth redirect URLs, and mandatory GDPR webhook subscriptions.

```toml
# shopify.app.toml — central app configuration
name = "My App"
client_id = "your_api_key_here"

[access_scopes]
scopes = "read_products,write_products,read_orders"

[auth]
redirect_urls = [
  "https://localhost/auth/callback",
  "https://localhost/auth/shopify/callback",
]

[webhooks]
# Update quarterly — see shopify.dev/docs/api/usage/versioning
api_version = "2025-04"

  [webhooks.subscriptions]
  # Mandatory GDPR webhooks
  [[webhooks.subscriptions]]
  topics = ["customers/data_request"]
  uri = "/webhooks"

  [[webhooks.subscriptions]]
  topics = ["customers/redact"]
  uri = "/webhooks"

  [[webhooks.subscriptions]]
  topics = ["shop/redact"]
  uri = "/webhooks"
```
