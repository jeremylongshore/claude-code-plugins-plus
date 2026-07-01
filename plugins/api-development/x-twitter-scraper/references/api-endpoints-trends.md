# Xquik REST API Endpoints: Trends

### List Trends

```
GET /x/trends?woeid=1&count=30
GET /trends?woeid=1&count=30
```

Metered. Plan access required. `/trends` is an alias of `/x/trends`. Cached, refreshes every 15 minutes.

**WOEIDs:** 1 (Worldwide), 23424977 (US), 23424975 (UK), 23424969 (Turkey), 23424950 (Spain), 23424829 (Germany), 23424819 (France), 23424856 (Japan), 23424848 (India), 23424768 (Brazil), 23424775 (Canada), 23424900 (Mexico).

**Response:**
```json
{
  "trends": [
    { "name": "#AI", "description": "...", "rank": 1, "query": "#AI" }
  ],
  "total": 30,
  "woeid": 1
}
```

---
