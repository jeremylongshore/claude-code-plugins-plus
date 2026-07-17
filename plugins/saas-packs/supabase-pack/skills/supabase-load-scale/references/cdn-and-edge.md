# Compute Upgrades, CDN for Storage, and Edge Function Regions

## Compute Size Selection Guide

| Tier | vCPU | RAM | Max Connections | Best For |
| ------ | ------ | ----- | ---------------- | ---------- |
| Micro (Free) | 2 shared | 1 GB | 60 | Development, prototypes |
| Small (Pro) | 2 dedicated | 2 GB | 90 | Low-traffic production |
| Medium | 2 dedicated | 4 GB | 120 | Growing apps, moderate traffic |
| Large | 4 dedicated | 8 GB | 160 | High-traffic, complex queries |
| XL | 8 dedicated | 16 GB | 240 | Large datasets, concurrent users |
| 2XL | 16 dedicated | 32 GB | 380 | Enterprise, heavy analytics |
| 4XL | 32 dedicated | 64 GB | 480 | Mission-critical, max throughput |

```bash
# Upgrade compute via CLI (requires Pro plan)
supabase projects update --experimental --compute-size small  # or medium, large, xl, 2xl, 4xl

# Check current compute size
supabase projects list
```

## CDN Caching for Storage Buckets

Public buckets are automatically served through Supabase's CDN. Optimize cache behavior with proper headers and transforms.

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
)

// Upload with cache-control headers for CDN optimization
async function uploadPublicAsset(
  bucket: string,
  path: string,
  file: File
) {
  const { data, error } = await supabase.storage
    .from(bucket)
    .upload(path, file, {
      cacheControl: '31536000',  // 1 year cache for immutable assets
      upsert: false,             // prevent accidental overwrites
      contentType: file.type,
    })

  if (error) throw new Error(`Upload failed: ${error.message}`)

  // Get the CDN-cached public URL
  const { data: { publicUrl } } = supabase.storage
    .from(bucket)
    .getPublicUrl(path, {
      transform: {
        width: 800,        // Image transforms are cached at the CDN edge
        quality: 80,
        format: 'webp',
      },
    })

  return { path: data.path, publicUrl }
}

// Bust cache by uploading to a new path (content-addressed)
import { createHash } from 'crypto'

async function uploadVersionedAsset(bucket: string, file: Buffer, ext: string) {
  const hash = createHash('sha256').update(file).digest('hex').slice(0, 12)
  const path = `assets/${hash}.${ext}`

  const { error } = await supabase.storage
    .from(bucket)
    .upload(path, file, {
      cacheControl: '31536000',
      upsert: false,
    })

  if (error && error.message !== 'The resource already exists') {
    throw new Error(`Versioned upload failed: ${error.message}`)
  }

  return supabase.storage.from(bucket).getPublicUrl(path).data.publicUrl
}
```

## Edge Function Regional Deployment

```bash
# Deploy to a specific region (closer to your users)
supabase functions deploy my-function --region us-east-1
supabase functions deploy my-function --region eu-west-1
supabase functions deploy my-function --region ap-southeast-1

# List available regions
supabase functions list

# Deploy all functions to a region
supabase functions deploy --region us-east-1
```

```typescript
// supabase/functions/geo-router/index.ts
// Edge Function that runs in the region closest to the user
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

Deno.serve(async (req) => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  // Edge Functions automatically run in the nearest region
  // Use this for latency-sensitive operations
  const { data, error } = await supabase
    .from('products')
    .select('id, name, price')
    .eq('region', req.headers.get('x-region') ?? 'us')
    .limit(20)

  if (error) {
    return new Response(JSON.stringify({ error: error.message }), { status: 500 })
  }

  return new Response(JSON.stringify(data), {
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, max-age=60',  // CDN caches the response
    },
  })
})
```
