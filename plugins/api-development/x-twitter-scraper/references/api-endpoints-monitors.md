# Xquik REST API Endpoints: Monitors

### Create Monitor

```
POST /monitors
```

**Body:**
```json
{
  "username": "elonmusk",
  "eventTypes": ["tweet.new", "tweet.reply", "tweet.quote"]
}
```

**Response:**
```json
{
  "id": "7",
  "username": "elonmusk",
  "xUserId": "44196397",
  "eventTypes": ["tweet.new", "tweet.reply", "tweet.quote"],
  "createdAt": "2026-02-24T10:30:00.000Z"
}
```

Event types: `tweet.new`, `tweet.quote`, `tweet.reply`, `tweet.retweet`, `webhook.test`.

Returns `409 monitor_already_exists` if the username is already monitored.

### List Monitors

```
GET /monitors
```

Returns all monitors (up to 200, no pagination). Response includes `monitors` array and `total` count.

### Get Monitor

```
GET /monitors/{id}
```

### Update Monitor

```
PATCH /monitors/{id}
```

**Body:** `{ "eventTypes": [...], "isActive": true|false }` (both optional)

### Delete Monitor

```
delete request to `/monitors/{id}`
```

Stops tracking and deletes all associated data.

### Keyword Monitors

```
GET /monitors/keywords
POST /monitors/keywords
GET /monitors/keywords/{id}
PATCH /monitors/keywords/{id}
delete request to `/monitors/keywords/{id}`
```

Create and manage ongoing keyword monitors. Treat these as persistent resources: confirm the keyword query, event delivery plan, and ongoing usage before creating or enabling one.

---
