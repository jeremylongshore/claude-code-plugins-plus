# Xquik REST API Endpoints: X Write

Write actions performed through connected X accounts. All endpoints are metered. Every request requires an `account` field (username or account ID) identifying which connected account to use.

### Create Tweet

```
POST /x/tweets
```

**Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `account` | string | Yes | Connected X username or account ID |
| `text` | string | No | Tweet text (280 chars, or 25,000 if `is_note_tweet` is true). Required unless `media` is provided |
| `reply_to_tweet_id` | string | No | Tweet ID to reply to |
| `attachment_url` | string | No | URL to attach as a card |
| `community_id` | string | No | Community ID to post into |
| `is_note_tweet` | boolean | No | Long-form note tweet (up to 25,000 chars) |
| `media` | string[] | No | Public image URLs to attach (max 4). `POST /x/media` returns `mediaUrl` values for this field |

**Response:** `{ tweetId, success: true }`

**Errors:** `502 x_write_failed`

### Delete Tweet

```
delete request to `/x/tweets/{id}`
```

**Body:** `{ "account": "username" }`

**Response:** `{ success: true }`

### Like Tweet

```
POST /x/tweets/{id}/like
```

**Body:** `{ "account": "username" }`

### Unlike Tweet

```
delete request to `/x/tweets/{id}/like`
```

**Body:** `{ "account": "username" }`

### Retweet

```
POST /x/tweets/{id}/retweet
```

**Body:** `{ "account": "username" }`

### Unretweet

```
delete request to `/x/tweets/{id}/retweet`
```

**Body:** `{ "account": "username" }`

### Follow User

```
POST /x/users/{id}/follow
```

**Body:** `{ "account": "username" }`

**Errors:** `502 x_write_failed`

### Unfollow User

```
delete request to `/x/users/{id}/follow`
```

**Body:** `{ "account": "username" }`

### Remove Follower

```
POST /x/users/{id}/remove-follower
```

Remove a user from your followers without blocking them.

**Body:** `{ "account": "username" }`

**Usage:** Metered per call.

### Send DM

```
POST /x/dm/{userId}
```

**Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `account` | string | Yes | Connected X username or account ID |
| `text` | string | Yes | Message text |
| `media_ids` | string[] | No | Media IDs to attach |
| `reply_to_message_id` | string | No | Message ID to reply to |

### Get DM History

```
GET /x/dm/{userId}/history
```

Get DM conversation history with a user. Requires a connected X account. Metered per returned result.

**Sensitive:** Returns private DM conversations. Confirm with user before calling. Forward to other tools only after explicit approval.

### Update Profile

```
PATCH /x/profile
```

**Body:** `{ "account": "username", "name": "...", "description": "...", "location": "...", "url": "..." }` (account required, others optional)

### Update Avatar

```
PATCH /x/profile/avatar
```

Update profile avatar. Max 700 KB, GIF/JPEG/PNG. Metered.

**Body:** FormData with `account` (required) and `file` (required, max 700 KB).

### Update Banner

```
PATCH /x/profile/banner
```

Update profile banner. Max 2 MB, GIF/JPEG/PNG. Metered.

**Body:** FormData with `account` (required) and `file` (required, max 2 MB).

### Upload Media

```
POST /x/media
```

**Body:** FormData with `account` (required), `file` (required), and `is_long_video` (optional boolean). Alternatively, JSON body with `account` (required) and `url` (required, direct media URL) for URL-based upload.

**Response:** Returns `mediaId`, `mediaUrl`, and `success`. Pass `mediaUrl` in the `media` array when creating a tweet.

### Create Community

```
POST /x/communities
```

**Body:** `{ "account": "username", "name": "...", "description": "..." }` (all required)

### Delete Community

```
delete request to `/x/communities/{id}`
```

**Body:** `{ "account": "username", "community_name": "..." }` (name required for confirmation)

### Join Community

```
POST /x/communities/{id}/join
```

**Body:** `{ "account": "username" }`

**Errors:** `409 already_member`

### Leave Community

```
delete request to `/x/communities/{id}/join`
```

**Body:** `{ "account": "username" }`

### Get Write Action Status

```
GET /x/write-actions/{id}
```

Check a pending write action by the ID returned from an earlier write response.

---
