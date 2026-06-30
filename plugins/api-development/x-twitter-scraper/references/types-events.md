# Xquik TypeScript Types: Events

```typescript

interface XquikEvent {
  id: string;
  type: EventType;
  monitorId: string;
  username: string;
  occurredAt: string;
  data: EventData;
  xEventId?: string;
}

// Tweet events (tweet.new, tweet.reply, tweet.quote, tweet.retweet)
interface TweetEventData {
  tweetId: string;
  text: string;
  metrics: {
    likes: number;
    retweets: number;
    replies: number;
  };
  // tweet.quote only
  quotedTweetId?: string;
  quotedUsername?: string;
  // tweet.reply only
  inReplyToTweetId?: string;
  inReplyToUsername?: string;
  // tweet.retweet only
  retweetedTweetId?: string;
  retweetedUsername?: string;
}

type EventData = TweetEventData;

interface EventList {
  events: XquikEvent[];
  hasMore: boolean;
  nextCursor?: string;
}

```
