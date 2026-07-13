Vercel deployment configuration for Shopify Remix apps, including environment variables and vercel.json setup.

```bash
# Set environment variables
vercel env add SHOPIFY_API_KEY production
vercel env add SHOPIFY_API_SECRET production
vercel env add SHOPIFY_SCOPES production
vercel env add SHOPIFY_APP_URL production

# Deploy
vercel --prod
```

```json
// vercel.json
{
  "framework": "remix",
  "env": {
    "SHOPIFY_API_KEY": "@shopify-api-key",
    "SHOPIFY_API_SECRET": "@shopify-api-secret"
  },
  "headers": [
    {
      "source": "/webhooks(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "*" }
      ]
    }
  ],
  "functions": {
    "app/**/*.ts": { "maxDuration": 25 }
  }
}
```

Update `shopify.app.toml` with your Vercel URL:

```toml
[auth]
redirect_urls = [
  "https://your-app.vercel.app/auth/callback"
]

application_url = "https://your-app.vercel.app"
```
