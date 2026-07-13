# Vercel Deployment

## Vercel Deployment

### Environment Setup

```bash
# Add Vercel secrets to Vercel
vercel secrets add vercel_api_key sk_live_***
vercel secrets add vercel_webhook_secret whsec_***

# Link to project
vercel link

# Deploy preview
vercel

# Deploy production
vercel --prod
```

### vercel.json Configuration

```json
{
  "env": {
    "VERCEL_API_KEY": "@vercel_api_key"
  },
  "functions": {
    "api/**/*.ts": {
      "maxDuration": 30
    }
  }
}
```
