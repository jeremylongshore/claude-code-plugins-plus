# Xquik TypeScript Types: Monitors

```typescript

interface Monitor {
  id: string;
  username: string;
  xUserId: string;
  eventTypes: EventType[];
  isActive: boolean;
  createdAt: string;
}

type EventType =
  | "tweet.new"
  | "tweet.quote"
  | "tweet.reply"
  | "tweet.retweet";

```
