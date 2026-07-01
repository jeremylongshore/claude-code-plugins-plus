# Xquik TypeScript Types: MCP: lookup-tweet

```typescript

interface McpTweetLookup {
  tweet: {
    id: string;               // Tweet ID
    text: string;             // Tweet text
    likeCount: number;        // Number of likes
    retweetCount: number;     // Number of retweets
    replyCount: number;       // Number of replies
    quoteCount: number;       // Number of quote tweets
    viewCount: number;        // Number of views
    bookmarkCount: number;    // Number of bookmarks
    media?: { mediaUrl: string; type: string; url: string }[];  // Attached photos/videos
  };
  author?: {                  // Tweet author details
    id: string;               // Author user ID
    username: string;         // Author X username
    followers: number;        // Author follower count
    verified: boolean;        // Whether the author is verified
  };
}

```
