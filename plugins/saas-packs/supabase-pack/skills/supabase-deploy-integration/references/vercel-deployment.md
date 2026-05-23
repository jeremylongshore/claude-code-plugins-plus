# Vercel Deployment

## Vercel Deployment

### Environment Setup

```bash
# Add Supabase secrets to Vercel
vercel secrets add supabase_api_key sk_live_***
vercel secrets add supabase_webhook_secret whsec_***

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
    "SUPABASE_API_KEY": "@supabase_api_key"
  },
  "functions": {
    "api/**/*.ts": {
      "maxDuration": 30
    }
  }
}
```
