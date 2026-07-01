# Xquik TypeScript Types: Download Media

```typescript

interface DownloadMediaRequest {
  tweetInput?: string;  // Tweet URL or numeric tweet ID (single mode)
  tweetIds?: string[];  // Array of tweet URLs or IDs (bulk mode, max 50). Exactly 1 of tweetInput or tweetIds required.
}

interface DownloadMediaSingleResponse {
  tweetId: string;      // Resolved tweet ID
  galleryUrl: string;   // Shareable gallery page URL
  cacheHit: boolean;    // true if served from cache (no usage consumed)
}

interface DownloadMediaBulkResponse {
  galleryUrl: string;   // Combined gallery page URL
  totalTweets: number;  // Number of tweets processed
  totalMedia: number;   // Total media items downloaded
}

```
