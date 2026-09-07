# Xquik TypeScript types: download media

```typescript

type NonEmptyTweetIds = [string, ...string[]];

type DownloadMediaRequest =
  | { tweetInput: string; tweetId?: never; tweetUrl?: never; tweetIds?: never }
  | { tweetInput?: never; tweetId: string; tweetUrl?: never; tweetIds?: never }
  | { tweetInput?: never; tweetId?: never; tweetUrl: string; tweetIds?: never }
  | { tweetInput?: never; tweetId?: never; tweetUrl?: never; tweetIds: NonEmptyTweetIds };

// Validate tweetIds.length <= 50 at runtime.

interface DownloadMediaSingleResponse {
  tweetId: string;      // Resolved tweet ID
  galleryUrl: string;   // Gallery page URL. Treat it as sensitive.
  cacheHit: boolean;    // True when the cache served the result without usage.
}

interface DownloadMediaBulkResponse {
  galleryUrl: string;   // Combined gallery page URL
  totalTweets: number;  // Number of tweets processed
  totalMedia: number;   // Total media items downloaded
}

```

Check gallery visibility before sharing its URL. Restrict recipients and set a
retention period. Prefer authenticated or expiring links when supported. Delete
the gallery after use when supported.
