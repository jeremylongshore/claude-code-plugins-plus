# Environment Configuration Files

Environment variable files and Shopify CLI TOML configs for dev, staging, and production.

```bash
# .env.development (git-ignored)
SHOPIFY_API_KEY=dev_api_key
SHOPIFY_API_SECRET=dev_api_secret
SHOPIFY_STORE=dev-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_dev_token
SHOPIFY_APP_URL=https://localhost:3000
SHOPIFY_API_VERSION=2025-04  # Update quarterly — see shopify.dev/docs/api/usage/versioning
NODE_ENV=development

# .env.staging (git-ignored)
SHOPIFY_API_KEY=staging_api_key
SHOPIFY_API_SECRET=staging_api_secret
SHOPIFY_STORE=staging-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_staging_token
SHOPIFY_APP_URL=https://staging.your-app.com
SHOPIFY_API_VERSION=2025-04  # Update quarterly — see shopify.dev/docs/api/usage/versioning
NODE_ENV=staging

# .env.production (never on disk — use secret manager)
# All values stored in Vault / AWS Secrets Manager / GCP Secret Manager
```

```toml
# shopify.app.dev.toml — development config
name = "My App (Dev)"
client_id = "dev_api_key"

[access_scopes]
scopes = "read_products,write_products,read_orders,write_orders"

[auth]
redirect_urls = ["https://localhost/auth/callback"]

[webhooks]
api_version = "2025-04"  # Update quarterly — see shopify.dev/docs/api/usage/versioning
```

```bash
# Switch between app configs
shopify app config use shopify.app.dev.toml
shopify app dev

shopify app config use shopify.app.toml  # production
shopify app deploy
```
