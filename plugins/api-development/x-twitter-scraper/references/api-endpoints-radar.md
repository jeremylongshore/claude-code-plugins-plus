# Xquik REST API Endpoints: Radar

### List Radar Items

```
GET /radar
```

Get trending topics and news from supported trend and news sources.

**Query parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `source` | string | Filter by public source: `google_trends`, `hacker_news`, `polymarket`, `wikipedia`, `github`, `reddit`. Omit to include all supported sources |
| `category` | string | Filter by category: `general`, `tech`, `dev`, `science`, `culture`, `politics`, `business`, `entertainment` |
| `limit` | number | Items per page (1-100, default 50) |
| `hours` | number | Look-back window in hours (1-72, default 6) |
| `region` | string | Region code: `US`, `GB`, `TR`, `ES`, `DE`, `FR`, `JP`, `IN`, `BR`, `CA`, `MX`, `global` (default) |

**Response:**
```json
{
  "items": [
    {
      "id": "12345",
      "title": "Claude 4.6 Released",
      "description": "Anthropic releases Claude 4.6...",
      "url": "https://example.com/article",
      "imageUrl": "https://example.com/image.png",
      "source": "hacker_news",
      "sourceId": "hn_12345",
      "category": "tech",
      "region": "global",
      "language": "en",
      "score": 450,
      "metadata": { "points": 450, "numberComments": 132, "author": "pgdev" },
      "publishedAt": "2026-03-05T10:00:00.000Z",
      "createdAt": "2026-03-05T10:05:00.000Z"
    }
  ],
  "hasMore": true,
  "nextCursor": "NDUwfDIwMjYtMDMtMDRUMDg6MzA6MDAuMDAwWnwxMjM0NQ=="
}
```

Fields: `id`, `title`, `description?`, `url?`, `imageUrl?`, `source`, `sourceId`, `category`, `region`, `language`, `score`, `metadata`, `publishedAt`, `createdAt`. Response includes `hasMore` and `nextCursor` for pagination.

---
