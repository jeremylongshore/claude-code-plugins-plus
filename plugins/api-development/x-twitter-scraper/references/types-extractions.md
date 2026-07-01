# Xquik TypeScript Types: Extractions

```typescript

type ExtractionToolType =
  | "article_extractor"
  | "community_extractor"
  | "community_moderator_explorer"
  | "community_post_extractor"
  | "community_search"
  | "favoriters"
  | "follower_explorer"
  | "following_explorer"
  | "list_follower_explorer"
  | "list_member_extractor"
  | "list_post_extractor"
  | "mention_extractor"
  | "people_search"
  | "post_extractor"
  | "quote_extractor"
  | "reply_extractor"
  | "repost_extractor"
  | "space_explorer"
  | "thread_extractor"
  | "tweet_search_extractor"
  | "user_likes"
  | "user_media"
  | "verified_follower_explorer";

interface ExtractionJob {
  id: string;
  toolType: ExtractionToolType;
  status: "pending" | "running" | "completed" | "failed";
  totalResults: number;
  targetTweetId?: string;
  targetUsername?: string;
  targetUserId?: string;
  targetCommunityId?: string;
  targetListId?: string;
  targetSpaceId?: string;
  searchQuery?: string;
  resultsLimit?: number; // Max results to extract. Stops early instead of fetching all. Omit for all.
  errorMessage?: string;
  createdAt: string;
  completedAt?: string;
}

interface ExtractionResult {
  id: string;
  xUserId: string;
  xUsername?: string;
  xDisplayName?: string;
  xFollowersCount?: number;
  xVerified?: boolean;
  xProfileImageUrl?: string;
  tweetId?: string;
  tweetText?: string;
  tweetCreatedAt?: string;
  createdAt: string;
}

interface ExtractionList {
  extractions: ExtractionJob[];
  hasMore: boolean;
  nextCursor?: string;
}

interface ExtractionEstimate {
  allowed: boolean;
  creditsAvailable: string;
  creditsRequired: string;
  source: "replyCount" | "retweetCount" | "quoteCount" | "followers" | "unknown";
  estimatedResults: number;
  resolvedXUserId?: string;
  error?: string;
}

interface CreateExtractionRequest {
  toolType: ExtractionToolType;
  targetTweetId?: string;
  targetUsername?: string;
  targetCommunityId?: string;
  targetListId?: string;
  targetSpaceId?: string;
  searchQuery?: string;
  resultsLimit?: number; // Max results to extract. Stops early instead of fetching all. Omit for all.
  // Tweet search filters (tweet_search_extractor only)
  fromUser?: string;
  toUser?: string;
  mentioning?: string;
  language?: string;
  sinceDate?: string;           // YYYY-MM-DD
  untilDate?: string;           // YYYY-MM-DD
  mediaType?: 'images' | 'videos' | 'gifs' | 'media';
  minFaves?: number;
  minRetweets?: number;
  minReplies?: number;
  verifiedOnly?: boolean;
  replies?: 'include' | 'exclude' | 'only';
  retweets?: 'include' | 'exclude' | 'only';
  exactPhrase?: string;
  excludeWords?: string;
  advancedQuery?: string;
}

```
