# Xquik REST API Endpoints: X API (Direct Lookups)

Metered operations that require account access.

### Get Tweet

```
GET /x/tweets/{id}
```

Returns full tweet with engagement metrics (likes, retweets, replies, quotes, views, bookmarks), author info (username, followers, verified status, profile picture), and optional attached media (photos/videos with URLs).

### Get Article

```
GET /x/articles/{tweetId}
```

Retrieve the full content of an X Article (long-form post) by numeric tweet ID. If the user gives an article URL, use the final status ID as `tweetId`. Returns title, body text with block-level formatting, cover image, inline images, and engagement metrics. Metered.

**Response:**
```json
{
  "title": "Why AI Will Transform Everything",
  "coverImage": "https://pbs.twimg.com/...",
  "bodyHtml": "<p>The future of AI...</p>",
  "likeCount": 5200,
  "retweetCount": 890,
  "replyCount": 245,
  "viewCount": 150000,
  "bookmarkCount": 1200,
  "author": {
    "id": "44196397",
    "username": "elonmusk",
    "name": "Elon Musk"
  }
}
```

### Search Tweets

```
GET /x/tweets/search?q={query}
```

Search using X syntax: keywords, `#hashtags`, `from:user`, `to:user`, `"exact phrases"`, `OR`, `-exclude`.

Returns tweet info with optional engagement metrics (likeCount, retweetCount, replyCount) and optional attached media. Some fields may be omitted if unavailable.

### Get User

```
GET /x/users/{id}
```

Returns profile info. `id` accepts either an X username without `@` or a numeric user ID. Fields `id`, `username`, `name` are always present. All other fields (`description`, `followers`, `following`, `verified`, `profilePicture`, `location`, `createdAt`, `statusesCount`) are optional and omitted when unavailable.

### Batch & Search Users

```
GET /x/users/batch?ids=44196397,783214
GET /x/users/search?q=founder
```

Batch lookup accepts up to 100 comma-separated numeric user IDs. User search returns matching profiles and may include a pagination cursor.

### Check Follower

```
GET /x/followers/check?source={username}&target={username}
```

Returns `isFollowing` and `isFollowedBy` for both directions.

### Get User Tweets

```
GET /x/users/{id}/tweets
```

Get a user's recent tweets by user ID. Metered per returned tweet.

### Batch Tweets

```
GET /x/tweets?ids=1893456789012345678,1893456789012345679
```

Get multiple tweets by comma-separated tweet IDs. Maximum 100 IDs.

### Get User Likes

```
GET /x/users/{id}/likes
```

Get tweets liked by a user. Metered per returned result.

### Get User Media

```
GET /x/users/{id}/media
```

Get a user's media tweets (tweets containing photos/videos). Metered per returned result.

### Get Tweet Favoriters

```
GET /x/tweets/{id}/favoriters
```

Get users who liked a tweet. Metered per returned result.

### Tweet Conversation & Engagement Lists

```
GET /x/tweets/{id}/quotes
GET /x/tweets/{id}/replies
GET /x/tweets/{id}/retweeters
GET /x/tweets/{id}/thread
```

Read quote tweets, replies, retweeters, or the conversation thread for a tweet. These are paginated read operations.

### User Social Graph Reads

```
GET /x/users/{id}/followers
GET /x/users/{id}/following
GET /x/users/{id}/mentions
GET /x/users/{id}/verified-followers
```

Read followers, following, mentions, and verified followers for a username or numeric user ID. These are paginated read operations.

### Get Mutual Followers

```
GET /x/users/{id}/followers-you-know
```

Get mutual followers (followers you know). Metered per returned result.

### X Lists

```
GET /x/lists/{id}/followers
GET /x/lists/{id}/members
GET /x/lists/{id}/tweets
```

Read list followers, members, or list timeline tweets by list ID.

### X Communities

```
GET /x/communities/search
GET /x/communities/tweets
GET /x/communities/{id}/info
GET /x/communities/{id}/members
GET /x/communities/{id}/moderators
GET /x/communities/{id}/tweets
```

Search communities and read community metadata, members, moderators, or tweets. Community writes are listed under X Write and require confirmation.

### Get Bookmarks

```
GET /x/bookmarks
```

Get bookmarked tweets. Requires a connected X account. Metered per returned result.

**Sensitive:** Returns private data. Confirm with user before calling.

### Get Bookmark Folders

```
GET /x/bookmarks/folders
```

Get bookmark folders. Requires a connected X account. Metered.

### Get Notifications

```
GET /x/notifications
```

Get notifications with type filter. Requires a connected X account. Metered per returned result.

**Sensitive:** Returns private data. Confirm with user before calling.

### Get Home Timeline

```
GET /x/timeline
```

Get home timeline. Requires a connected X account. Metered per returned result.

**Sensitive:** Returns private data. Confirm with user before calling.

---
