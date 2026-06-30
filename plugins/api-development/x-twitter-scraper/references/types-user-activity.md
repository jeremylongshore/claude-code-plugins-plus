# Xquik TypeScript Types: User Activity

```typescript

interface UserTweetsResponse {
  tweets: Tweet[];
  has_next_page: boolean;
  next_cursor?: string;
}

interface UserLikesResponse {
  tweets: Tweet[];
  has_next_page: boolean;
  next_cursor?: string;
}

interface UserMediaResponse {
  tweets: Tweet[];
  has_next_page: boolean;
  next_cursor?: string;
}

interface TweetFavoritersResponse {
  users: UserProfile[];
  has_next_page: boolean;
  next_cursor?: string;
}

interface FollowersYouKnowResponse {
  users: UserProfile[];
  has_next_page: boolean;
  next_cursor?: string;
}

```
