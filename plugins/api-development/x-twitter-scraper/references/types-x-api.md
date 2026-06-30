# Xquik TypeScript Types: X API

```typescript

interface TweetMediaItem {
  mediaUrl: string;
  type: string;       // "photo" | "video" | "animated_gif"
  url: string;
}

interface Tweet {
  id: string;
  text: string;
  createdAt?: string;
  retweetCount: number;
  replyCount: number;
  likeCount: number;
  quoteCount: number;
  viewCount: number;
  bookmarkCount: number;
  media?: TweetMediaItem[];
}

interface TweetAuthor {
  id: string;
  username: string;
  followers: number;
  verified: boolean;
  profilePicture?: string;
}

interface TweetSearchResult {
  id: string;
  text: string;
  createdAt: string;
  likeCount: number;    // Omitted if unavailable
  retweetCount: number; // Omitted if unavailable
  replyCount: number;   // Omitted if unavailable
  media?: TweetMediaItem[];
  author: {
    id: string;
    username: string;
    name: string;
    verified: boolean;
  };
}

interface UserProfile {
  id: string;
  username: string;
  name: string;
  description?: string;
  followers?: number;
  following?: number;
  verified?: boolean;
  profilePicture?: string;
  location?: string;
  createdAt?: string;
  statusesCount?: number;
}

interface FollowerCheck {
  sourceUsername: string;
  targetUsername: string;
  isFollowing: boolean;
  isFollowedBy: boolean;
}

```
