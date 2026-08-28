# Analytics & Feedback Loop

## Performance Tracking

### Upload-Post Analytics API

**Platform analytics** (followers, impressions, reach, profile views):
```
GET https://api.upload-post.com/api/analytics/{profile}?platforms=tiktok,instagram
Authorization: Apikey {apiKey}
```

Response:
```json
{
  "tiktok": {
    "followers": 1071,
    "reach": 0,
    "impressions": 6522,
    "profileViews": 0,
    "reach_timeseries": [
      { "date": "2026-02-11", "value": 773 },
      { "date": "2026-02-12", "value": 190 }
    ]
  },
  "instagram": {
    "followers": 523,
    "impressions": 12500,
    "profileViews": 89,
    "reach": 8700,
    "reach_timeseries": [...]
  }
}
```

**Upload history** (per-post tracking with request_ids):
```
GET https://api.upload-post.com/api/uploadposts/history?page=1&limit=50&profile_username={profile}
Authorization: Apikey {apiKey}
```

Response:
```json
{
  "history": [
    {
      "profile_username": "upload_post",
      "platform": "tiktok",
      "media_type": "image",
      "upload_timestamp": "2026-02-15T14:30:00Z",
      "success": true,
      "platform_post_id": "7605531854921354518",
      "post_url": "https://www.tiktok.com/@user/video/7605531854921354518",
      "post_title": "Caption text...",
      "request_id": "abc123def456",
      "request_total_platforms": 2
    }
  ]
}
```

**Upload status** (check async upload progress):
```
GET https://api.upload-post.com/api/uploadposts/status?request_id={request_id}
Authorization: Apikey {apiKey}
```

### Key Difference from Postiz

Upload-Post automatically tracks posts by `request_id`. No manual video-ID linking is needed:
- When you upload via `POST /upload_photos`, you get a `request_id`
- Upload history includes the `request_id`, platform-specific post IDs, and post URLs
- Analytics are tracked at the platform level (followers, impressions, reach)
- No release-ID connection step — Upload-Post handles it automatically

### RevenueCat Integration (Optional)

If the user has RevenueCat, track conversions from TikTok:
- Downloads → Trial starts → Paid conversions
- UTM parameters in App Store link
- Compare conversion spikes with post timing

## The Feedback Loop

### After Every Post (24h)
Record in `hook-performance.json`:
```json
{
  "hooks": [
    {
      "requestId": "abc123def456",
      "text": "boyfriend said flat looks like catalogue",
      "date": "2026-02-15",
      "platforms": {
        "tiktok": { "success": true, "postUrl": "..." },
        "instagram": { "success": true, "postUrl": "..." }
      },
      "conversions": 4,
      "cta": "Download App — link in bio",
      "lastChecked": "2026-02-16"
    }
  ]
}
```

### Weekly Review
1. Check platform analytics deltas (impressions, followers growth)
2. Review upload history for successes/failures
3. Identify top hooks by conversion rate (if RevenueCat connected)
4. Check if any hook CATEGORY consistently wins
5. Update prompt templates with learnings

### Decision Rules (based on platform impressions + conversions)

| Impressions Trend | Action |
|-------|--------|
| Growing (5K+/day) | DOUBLE DOWN — make 3 variations immediately |
| Steady (1K-5K/day) | Good — keep in rotation, test tweaks |
| Declining (<1K/day) | Try radically different approach |

### What to Vary When Iterating
- **Same hook, different person:** "landlord" → "mum" → "boyfriend"
- **Same structure, different room/feature:** bedroom → kitchen → bathroom
- **Same images, different text:** proven images can be reused with new hooks
- **Same hook, different time:** morning vs evening posting

## Conversion Tracking

### Funnel
```
Views → Profile Visits → Link Clicks → App Store → Download → Trial → Paid
```

### Benchmarks
- 1% conversion (views → download) = average
- 1.5-3% = good
- 3%+ = great

### Attribution Tips
- Track download spikes within 24h of viral post
- Use unique UTM links per campaign if possible
- RevenueCat `$attribution` for source tracking
- Compare weekly MRR growth with weekly view totals

## Daily Analytics Cron

Set up a cron job to run every morning before the first post (e.g. 7:00 AM user's timezone):

```
Task: node scripts/daily-report.js --config tiktok-marketing/config.json --days 3
Output: tiktok-marketing/reports/YYYY-MM-DD.md
```

The daily report:
1. Fetches platform analytics from Upload-Post (impressions, followers, reach timeseries)
2. Fetches upload history for the last N days (per-post success/failure, post URLs)
3. If RevenueCat is connected, pulls conversion events (trials, purchases) in the same window
4. Cross-references: maps conversion timestamps to post upload times (24-72h attribution window)
5. Applies the diagnostic framework:
   - High views + High conversions → SCALE (make variations)
   - High views + Low conversions → FIX CTA (hook works, downstream is broken)
   - Low views + High conversions → FIX HOOKS (content converts, needs more eyeballs)
   - Low views + Low conversions → FULL RESET (try radically different approach)
6. Suggests new hooks based on what's working
7. Updates `hook-performance.json` with latest data
8. Messages the user with a summary

### Why 3 Days?
- TikTok posts peak at 24-48 hours (not instant like Twitter)
- Conversion attribution takes up to 72 hours (user sees post → downloads → trials → pays)
- 3-day window captures the full lifecycle of each post

### Multi-Platform Advantage
Upload-Post sends to TikTok + Instagram (and any other connected platforms) in a single API call.
The analytics endpoint returns per-platform data, so you can compare performance across platforms
and identify where your content resonates most.
