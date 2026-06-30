# Xquik TypeScript Types: X Articles

```typescript

interface Article {
  title: string;
  coverImage?: string;
  bodyHtml: string;
  likeCount: number;
  retweetCount: number;
  replyCount: number;
  viewCount: number;
  bookmarkCount: number;
  author: {
    id: string;
    username: string;
    name: string;
  };
}

```
