# Full Deployment Examples

Two complete, copy-ready examples: a minimal Express server that works on any
platform, and a platform-agnostic deploy script. Both import the modules from
[implementation.md](implementation.md) and the error handler from
[production-error-monitoring.md](production-error-monitoring.md).

## Minimal Express Server (deploy anywhere)

```typescript
import express from 'express';
import { getNotionClient } from './notion-client';
import { rateLimiter } from './rate-limiter';
import { healthCheck } from './health';
import { logNotionError } from './notion-error-handler';

const app = express();
app.use(express.json());

app.get('/health', async (_req, res) => {
  const result = await healthCheck();
  res.status(result.status === 'healthy' ? 200 : 503).json(result);
});

app.post('/api/query', async (req, res) => {
  const { databaseId, filter } = req.body;
  try {
    const notion = getNotionClient();
    const data = await rateLimiter.execute(() =>
      notion.databases.query({ database_id: databaseId, filter })
    );
    res.json({ results: data.results, hasMore: data.has_more });
  } catch (error) {
    logNotionError(error, { route: '/api/query' });
    res.status(500).json({ error: 'Query failed' });
  }
});

app.listen(Number(process.env.PORT) || 3000);
```

## Deploy Script (platform-agnostic)

```bash
#!/bin/bash
set -euo pipefail

PLATFORM="${1:?Usage: deploy.sh [vercel|railway|fly]}"

echo "Building..."
npm run build

case "$PLATFORM" in
  vercel)
    vercel env add NOTION_TOKEN production 2>/dev/null || true
    vercel --prod
    ;;
  railway)
    railway variables set NOTION_TOKEN="$NOTION_TOKEN"
    railway up
    ;;
  fly)
    fly secrets set NOTION_TOKEN="$NOTION_TOKEN"
    fly deploy
    ;;
  *)
    echo "Unknown platform: $PLATFORM" >&2
    exit 1
    ;;
esac

echo "Verifying health..."
sleep 5
curl -sf "$(echo "$PLATFORM" | xargs -I{} echo "https://my-notion-service.{}.dev/health")" || echo "Health check pending — verify manually"
```
