#!/bin/bash
# Publish carousel to TikTok + Instagram via Upload-Post API
# Docs: https://docs.upload-post.com/api/upload-photo
# Usage: ./publish-carousel.sh

set -e

CAROUSEL_DIR="/tmp/carousel"
CAPTION_FILE="$CAROUSEL_DIR/caption.txt"
ANALYSIS_FILE="$CAROUSEL_DIR/analysis.json"

UPLOADPOST_URL="https://api.upload-post.com"
UPLOADPOST_TOKEN="${UPLOADPOST_TOKEN:?Error: UPLOADPOST_TOKEN is not set}"
DEFAULT_USER="${UPLOADPOST_USER:?Error: UPLOADPOST_USER is not set}"

# Verify slides
SLIDES=""
for i in 1 2 3 4 5 6; do
    if [ -f "$CAROUSEL_DIR/slide-$i.jpg" ]; then
        SLIDES="$SLIDES $CAROUSEL_DIR/slide-$i.jpg"
    fi
done

if [ -z "$SLIDES" ]; then
    echo "❌ No slides found in $CAROUSEL_DIR/"
    exit 1
fi

SLIDE_COUNT=$(echo $SLIDES | wc -w)
echo "═══════════════════════════════════════════════════════════════"
echo "📤 PUBLISHING CAROUSEL TO TIKTOK + INSTAGRAM"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📁 Slides: $SLIDE_COUNT images"
echo "👤 User: $DEFAULT_USER"

# Load caption
if [ -f "$CAPTION_FILE" ]; then
    CAPTION=$(cat "$CAPTION_FILE")
else
    CAPTION="Check this out! 🔥 #viral #fyp"
fi

# Caption para Instagram (max 2200 chars)
CAPTION_TRUNCATED=$(echo "$CAPTION" | head -c 2000)

# TikTok title (max 90 chars) - first line + hashtags
TIKTOK_TITLE=$(echo "$CAPTION" | head -1 | head -c 60)
TIKTOK_TITLE="$TIKTOK_TITLE #viral #fyp"

echo ""
echo "📝 Caption:"
echo "$CAPTION_TRUNCATED" | head -5
echo "..."
echo ""

# Extract product name from analysis
PRODUCT_NAME="carousel"
if [ -f "$ANALYSIS_FILE" ]; then
    PRODUCT_NAME=$(jq -r '.storytelling.productName // "carousel"' "$ANALYSIS_FILE")
fi

# Build curl command per documentation
echo "🚀 Sending to Upload-Post API..."
echo "   🎵 auto_add_music: enabled"
echo "   🌍 privacy_level: PUBLIC_TO_EVERYONE"
echo ""

# Create command
CMD="curl -s -X POST '$UPLOADPOST_URL/api/upload_photos'"
CMD="$CMD -H 'Authorization: Apikey $UPLOADPOST_TOKEN'"
CMD="$CMD -F 'user=$DEFAULT_USER'"
CMD="$CMD -F 'platform[]=tiktok'"
CMD="$CMD -F 'platform[]=instagram'"
CMD="$CMD -F 'title=$CAPTION_TRUNCATED'"
CMD="$CMD -F 'tiktok_title=$TIKTOK_TITLE'"
CMD="$CMD -F 'auto_add_music=true'"
CMD="$CMD -F 'privacy_level=PUBLIC_TO_EVERYONE'"
CMD="$CMD -F 'media_type=IMAGE'"
CMD="$CMD -F 'async_upload=true'"

# Add photos
for slide in $SLIDES; do
    CMD="$CMD -F 'photos[]=@$slide'"
done

# Execute
RESPONSE=$(eval $CMD)

echo "📨 API Response:"
echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"

# Extraer request_id
REQUEST_ID=$(echo "$RESPONSE" | jq -r '.request_id // empty' 2>/dev/null)
SUCCESS=$(echo "$RESPONSE" | jq -r '.success // false' 2>/dev/null)

if [ "$SUCCESS" = "true" ] && [ -n "$REQUEST_ID" ]; then
    echo ""
    echo "✅ Upload sent!"
    echo "   Request ID: $REQUEST_ID"
    
    # Save post info for analytics tracking
    POST_INFO="{
  \"request_id\": \"$REQUEST_ID\",
  \"platforms\": [\"tiktok\", \"instagram\"],
  \"product\": \"$PRODUCT_NAME\",
  \"slides\": $SLIDE_COUNT,
  \"timestamp\": \"$(date -Iseconds)\",
  \"user\": \"$DEFAULT_USER\",
  \"caption\": $(echo "$CAPTION_TRUNCATED" | jq -Rs .)
}"
    echo "$POST_INFO" > "$CAROUSEL_DIR/post-info.json"
    
    echo ""
    echo "   🎵 TikTok: auto_add_music enabled ✅"
    echo ""
    echo "   ⚠️  INSTAGRAM: Remember to go to the app and add viral music!"
    echo "       1. Open Instagram → Your profile → The post"
    echo "       2. Edit → Add music"
    echo "       3. Search for a viral song/trending"
    echo ""
    echo "   📊 Info saved to: $CAROUSEL_DIR/post-info.json"
    
    # ═══════════════════════════════════════════════════════════════
    # UPDATE HOOK LEDGER WITH IMAGE PROMPT TRACKING
    # ═══════════════════════════════════════════════════════════════
    LEDGER_FILE="$(dirname "$0")/../hook-ledger.json"
    HOOK_INFO_FILE="$CAROUSEL_DIR/hook-info.json"
    
    if [ -f "$HOOK_INFO_FILE" ] && [ -f "$LEDGER_FILE" ]; then
        echo ""
        echo "   📒 Updating hook ledger..."
        
        # Read hook info
        HOOK_TYPE=$(jq -r '.hook_type // "unknown"' "$HOOK_INFO_FILE")
        HOOK_TEXT=$(jq -r '.hook_text // ""' "$HOOK_INFO_FILE")
        IMAGE_PROMPT=$(jq -r '.image_prompt // ""' "$HOOK_INFO_FILE")
        VISUAL_STYLE=$(jq -r '.visual_style // ""' "$HOOK_INFO_FILE")
        COLORS=$(jq -r '.colors // ""' "$HOOK_INFO_FILE")
        
        # Create new entry
        NEW_ENTRY=$(jq -n \
            --arg date "$(date +%Y-%m-%d)" \
            --arg type "$HOOK_TYPE" \
            --arg hook_text "$HOOK_TEXT" \
            --arg request_id "$REQUEST_ID" \
            --arg image_prompt "$IMAGE_PROMPT" \
            --arg visual_style "$VISUAL_STYLE" \
            --arg colors "$COLORS" \
            '{date: $date, type: $type, hook_text: $hook_text, request_id: $request_id, image_prompt: $image_prompt, visual_style: $visual_style, colors: $colors}')
        
        # Append to ledger
        jq --argjson entry "$NEW_ENTRY" '.hooks += [$entry]' "$LEDGER_FILE" > "${LEDGER_FILE}.tmp" && \
            mv "${LEDGER_FILE}.tmp" "$LEDGER_FILE"
        
        echo "   ✅ Ledger updated with image prompt tracking"
    fi
else
    echo ""
    echo "⚠️ Check API response"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
