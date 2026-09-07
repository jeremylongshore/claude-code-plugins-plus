# Performance Monitoring & Before/After Impact

Instrument the crawl so you can see throughput in the logs, then use the
comparison table to judge whether an optimization was worth it.

## Performance Monitoring in Actors

```typescript
import { Actor } from 'apify';
import { log } from 'crawlee';

// Log performance metrics during the crawl
let processedCount = 0;
const startTime = Date.now();

const crawler = new CheerioCrawler({
  requestHandler: async ({ request, $ }) => {
    processedCount++;

    if (processedCount % 100 === 0) {
      const elapsed = (Date.now() - startTime) / 1000;
      const rate = processedCount / (elapsed / 60);
      log.info(`Progress: ${processedCount} pages | ${rate.toFixed(1)} pages/min`);
    }

    await Actor.pushData({
      url: request.url,
      title: $('title').text().trim(),
    });
  },
});
```

## Performance Comparison

| Optimization | Before | After | Impact |
|-------------|--------|-------|--------|
| Cheerio instead of Playwright | 3 pages/min | 30 pages/min | 10x speed |
| Block images/CSS | 5 pages/min | 12 pages/min | 2.4x speed |
| Increase concurrency | 5 pages/min | 25 pages/min | 5x speed |
| Reduce memory 4GB to 512MB | $0.04/run | $0.005/run | 8x cost savings |
| Batch dataset pushes | 1000 API calls | 1 API call | Eliminates rate limits |
