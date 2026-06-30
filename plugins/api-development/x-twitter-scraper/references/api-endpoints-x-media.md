# Xquik REST API Endpoints: X Media (Download)

### Download Media

```
POST /x/media/download
```

Download images, videos, and GIFs from tweets. Single or bulk (up to 50). Returns a shareable gallery URL.

**Body:** Provide either `tweetInput` (single tweet) or `tweetIds` (bulk). Exactly 1 is required.

| Field | Type | Description |
|-------|------|-------------|
| `tweetInput` | string | Tweet URL or numeric tweet ID for a single download. Accepts `x.com` and `twitter.com` URL formats |
| `tweetIds` | string[] | Array of tweet URLs or IDs for bulk download. Maximum 50 items. Returns a single combined gallery |

**Response (single):**
```json
{
  "tweetId": "1893456789012345678",
  "galleryUrl": "https://xquik.com/g/abc123",
  "cacheHit": false
}
```

**Response (bulk):**
```json
{
  "galleryUrl": "https://xquik.com/g/def456",
  "totalTweets": 3,
  "totalMedia": 7
}
```

First download is metered. Subsequent requests for the same tweet return cached URLs when `cacheHit: true`. All downloads are saved to shareable gallery pages under `https://xquik.com/g/{token}`.

Returns `400 no_media` if the tweet has no downloadable media. Returns `400 too_many_tweets` if bulk array exceeds 50 items.

---
