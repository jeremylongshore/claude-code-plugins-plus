#!/bin/bash
# Get analytics for published posts via Upload-Post API
# Docs: https://docs.upload-post.com/api/get-analytics
# Usage: ./check-analytics.sh [days]

UPLOADPOST_URL="https://api.upload-post.com"
UPLOADPOST_TOKEN="${UPLOADPOST_TOKEN:?Error: UPLOADPOST_TOKEN is not set}"
DEFAULT_USER="${UPLOADPOST_USER:?Error: UPLOADPOST_USER is not set}"
DAYS="${1:-7}"
CAROUSEL_DIR="/tmp/carousel"

echo "═══════════════════════════════════════════════════════════════"
echo "📊 TIKTOK ANALYTICS - Last $DAYS days"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "👤 Profile: $DEFAULT_USER"
echo ""

# ═══════════════════════════════════════════════════════════════
# 1. TikTok profile analytics
# GET /api/analytics/{profile_username}?platforms=tiktok
# ═══════════════════════════════════════════════════════════════
echo "📈 TikTok profile analytics..."
PROFILE_ANALYTICS=$(curl -s -H "Authorization: Apikey $UPLOADPOST_TOKEN" \
    "$UPLOADPOST_URL/api/analytics/$DEFAULT_USER?platforms=tiktok")

if echo "$PROFILE_ANALYTICS" | jq -e '.tiktok' >/dev/null 2>&1; then
    echo ""
    echo "🎵 TikTok:"
    echo "$PROFILE_ANALYTICS" | jq -r '.tiktok | 
      "   👥 Followers: \(.followers // "N/A")",
      "   👀 Impressions: \(.impressions // "N/A")",
      "   ❤️ Likes: \(.likes // "N/A")",
      "   💬 Comments: \(.comments // "N/A")",
      "   🔄 Shares: \(.shares // "N/A")"
    ' 2>/dev/null
else
    echo "   ⚠️ No TikTok data"
    echo "$PROFILE_ANALYTICS" | jq . 2>/dev/null | head -10
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# 2. Total impressions (last N days)
# GET /api/uploadposts/total-impressions/{profile_username}
# ═══════════════════════════════════════════════════════════════
echo "📊 Total impressions (last $DAYS days)..."

# Calculate dates
END_DATE=$(date +%Y-%m-%d)
START_DATE=$(date -d "$DAYS days ago" +%Y-%m-%d 2>/dev/null || date -v-${DAYS}d +%Y-%m-%d)

IMPRESSIONS=$(curl -s -H "Authorization: Apikey $UPLOADPOST_TOKEN" \
    "$UPLOADPOST_URL/api/uploadposts/total-impressions/$DEFAULT_USER?platform=tiktok&start_date=$START_DATE&end_date=$END_DATE&breakdown=true")

if echo "$IMPRESSIONS" | jq -e '.success' >/dev/null 2>&1; then
    TOTAL=$(echo "$IMPRESSIONS" | jq -r '.total_impressions // 0')
    echo ""
    echo "   📈 Total impressions: $TOTAL"
    
    # Show per day if data available
    echo "$IMPRESSIONS" | jq -r '
      if .per_day then
        .per_day | to_entries | sort_by(.key) | reverse | .[:5][] |
        "   \(.key): \(.value) views"
      else empty end
    ' 2>/dev/null
else
    echo "   ⚠️ No impressions data"
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# 3. Specific post analytics (if post-info.json exists)
# GET /api/uploadposts/post-analytics/{request_id}
# ═══════════════════════════════════════════════════════════════
POST_INFO_FILE="$CAROUSEL_DIR/post-info.json"
if [ -f "$POST_INFO_FILE" ]; then
    REQUEST_ID=$(jq -r '.request_id // empty' "$POST_INFO_FILE")
    
    if [ -n "$REQUEST_ID" ]; then
        echo "📝 Analytics of last published carousel..."
        echo "   Request ID: $REQUEST_ID"
        
        POST_ANALYTICS=$(curl -s -H "Authorization: Apikey $UPLOADPOST_TOKEN" \
            "$UPLOADPOST_URL/api/uploadposts/post-analytics/$REQUEST_ID")
        
        if echo "$POST_ANALYTICS" | jq -e '.success' >/dev/null 2>&1; then
            echo ""
            # TikTok
            echo "$POST_ANALYTICS" | jq -r '
              .platforms.tiktok | 
              if . and .success then
                "   🎵 TikTok:",
                "      URL: \(.post_url // "pending")",
                "      👀 Views: \(.post_metrics.views // 0)",
                "      ❤️ Likes: \(.post_metrics.likes // 0)",
                "      💬 Comments: \(.post_metrics.comments // 0)"
              else empty end
            ' 2>/dev/null
            
            # Instagram
            echo "$POST_ANALYTICS" | jq -r '
              .platforms.instagram | 
              if . and .success then
                "   📸 Instagram:",
                "      URL: \(.post_url // "pendiente")",
                "      👀 Reach: \(.post_metrics.reach // 0)",
                "      ❤️ Likes: \(.post_metrics.likes // 0)",
                "      💬 Comments: \(.post_metrics.comments // 0)"
              else empty end
            ' 2>/dev/null
        else
            echo "   ⏳ Analytics not yet available (wait a few hours)"
        fi
    fi
fi

echo ""

# ═══════════════════════════════════════════════════════════════
# 4. Save snapshot for learn-from-analytics.js
# ═══════════════════════════════════════════════════════════════
SNAPSHOT_FILE="$CAROUSEL_DIR/analytics-snapshot.json"
echo "{
  \"timestamp\": \"$(date -Iseconds)\",
  \"days\": $DAYS,
  \"user\": \"$DEFAULT_USER\",
  \"profile\": $PROFILE_ANALYTICS,
  \"impressions\": $IMPRESSIONS
}" > "$SNAPSHOT_FILE" 2>/dev/null || echo "{}" > "$SNAPSHOT_FILE"

echo "💾 Snapshot saved to: $SNAPSHOT_FILE"
echo ""
echo "═══════════════════════════════════════════════════════════════"
