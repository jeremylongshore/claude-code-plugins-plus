# Platform-Specific Parameters

## TikTok

| Parameter | Type | Description |
|-----------|------|-------------|
| `tiktok_title` | String | Override title for TikTok |
| `post_mode` | String | `DIRECT_POST` (default) or `MEDIA_UPLOAD` (draft) |
| `privacy_level` | String | `PUBLIC_TO_EVERYONE`, `MUTUAL_FOLLOW_FRIENDS`, `FOLLOWER_OF_CREATOR`, `SELF_ONLY` |
| `auto_add_music` | Boolean | Add background music to photos |
| `disable_comment` | Boolean | Disable comments |
| `brand_content_toggle` | Boolean | Paid partnership content |
| `photo_cover_index` | Integer | Cover photo index (0-based) |

## Instagram

| Parameter | Type | Description |
|-----------|------|-------------|
| `instagram_title` | String | Override title |
| `media_type` | String | `IMAGE`, `STORIES`, `REELS` |
| `collaborators` | String | Comma-separated usernames |
| `user_tags` | String | Comma-separated users to tag |
| `location_id` | String | Instagram location ID |

## YouTube

| Parameter | Type | Description |
|-----------|------|-------------|
| `youtube_title` | String | Video title |
| `youtube_description` | String | Video description |
| `privacy_status` | String | `public`, `private`, `unlisted` |
| `category_id` | String | YouTube category ID |
| `tags` | Array | Video tags |
| `made_for_kids` | Boolean | COPPA compliance |
| `playlist_id` | String | Add to playlist |

## LinkedIn

| Parameter | Type | Description |
|-----------|------|-------------|
| `linkedin_title` | String | Override title |
| `visibility` | String | `PUBLIC`, `CONNECTIONS`, `LOGGED_IN` |
| `target_linkedin_page_id` | String | Organization/page URN |

Get page IDs: `GET /api/uploadposts/linkedin/pages`

## Facebook

| Parameter | Type | Description |
|-----------|------|-------------|
| `facebook_title` | String | Override title |
| `facebook_page_id` | String | Page ID (required for pages) |
| `facebook_media_type` | String | `POSTS` or `STORIES` |

Get page IDs: `GET /api/uploadposts/facebook/pages`

Note: Personal profiles not supported by Meta API - only Pages.

## X (Twitter)

| Parameter | Type | Description |
|-----------|------|-------------|
| `x_title` | String | Override title |
| `x_long_text_as_post` | Boolean | Post long text as single post (default: thread) |
| `reply_settings` | String | `following`, `mentionedUsers`, `subscribers`, `verified` |
| `reply_to_id` | String | Tweet ID to reply to |
| `community_id` | String | Post to community |
| `tagged_user_ids` | Array | Users to tag in photos (max 10) |

Thread behavior: Long text auto-splits at 280 chars. Media attaches to first tweet only.

## Threads

| Parameter | Type | Description |
|-----------|------|-------------|
| `threads_title` | String | Override title |

Supports mixed carousels (photos + videos).

## Pinterest

| Parameter | Type | Description |
|-----------|------|-------------|
| `pinterest_title` | String | Pin title |
| `pinterest_board_id` | String | Target board ID (required) |
| `pinterest_link` | String | Destination link |
| `pinterest_alt_text` | String | Alt text for image |

Get board IDs: `GET /api/uploadposts/pinterest/boards`

## Reddit

| Parameter | Type | Description |
|-----------|------|-------------|
| `reddit_title` | String | Post title |
| `subreddit` | String | Target subreddit (required) |
| `reddit_flair_id` | String | Flair ID |
| `nsfw` | Boolean | Mark as NSFW |
| `spoiler` | Boolean | Mark as spoiler |

## Bluesky

| Parameter | Type | Description |
|-----------|------|-------------|
| `bluesky_title` | String | Override title |
| `alt_text` | String | Alt text for images |

Limits: 4 images max, 1MB per image, 50 uploads/day.

## Common Parameters (All Platforms)

| Parameter | Type | Description |
|-----------|------|-------------|
| `first_comment` | String | Auto-post first comment (Instagram, Facebook, Threads, Bluesky, Reddit, X, YouTube) |
| `async_upload` | Boolean | Background processing |
| `scheduled_date` | String | ISO-8601 schedule time |
| `timezone` | String | IANA timezone for schedule |
