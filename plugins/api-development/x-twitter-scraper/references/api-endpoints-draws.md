# Xquik REST API Endpoints: Draws

### Create Draw

```
POST /draws
```

Run a giveaway draw from a tweet. Picks random winners from replies.

**Body:**
```json
{
  "tweetUrl": "https://x.com/user/status/1893456789012345678",
  "winnerCount": 3,
  "backupCount": 2,
  "uniqueAuthorsOnly": true,
  "mustRetweet": true,
  "mustFollowUsername": "burakbayir",
  "filterMinFollowers": 100,
  "filterAccountAgeDays": 30,
  "filterLanguage": "en",
  "requiredKeywords": ["giveaway"],
  "requiredHashtags": ["#contest"],
  "requiredMentions": ["@xquik"]
}
```

All filter fields are optional. Only `tweetUrl` is required.

**Response:**
```json
{
  "id": "42",
  "tweetId": "1893456789012345678",
  "tweetUrl": "https://x.com/user/status/1893456789012345678",
  "tweetText": "Like & RT to enter! Picking 3 winners tomorrow.",
  "tweetAuthorUsername": "xquik",
  "tweetLikeCount": 4200,
  "tweetRetweetCount": 1800,
  "tweetReplyCount": 1500,
  "tweetQuoteCount": 120,
  "status": "completed",
  "totalEntries": 1500,
  "validEntries": 890,
  "createdAt": "2026-02-24T10:00:00.000Z",
  "drawnAt": "2026-02-24T10:01:00.000Z"
}
```

### List Draws

```
GET /draws
```

Cursor-paginated. Returns compact draw objects.

### Get Draw

```
GET /draws/{id}
```

Returns full draw details including winners.

### Export Draw

```
GET /draws/{id}/export?format=csv&type=winners
```

Formats: `csv`, `json`, `md`, `md-document`, `pdf`, `txt`, `xlsx`. Types: `winners` (default), `entries`. Entry exports capped at 100,000 rows (PDF capped at 10,000).

---
