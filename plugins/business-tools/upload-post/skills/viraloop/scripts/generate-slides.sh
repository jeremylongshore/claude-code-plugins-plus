#!/bin/bash
# Generate slides v4 - Visual novelty + hook categories + anti-stock
set -e

CAROUSEL_DIR="/tmp/carousel"
ANALYSIS_FILE="$CAROUSEL_DIR/analysis.json"
HOOKS_DIR="$CAROUSEL_DIR/hooks"
UV_BIN="${HOME}/.local/bin/uv"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NANO_SCRIPT="$SCRIPT_DIR/generate_image.py"

# Parse arguments
HOOK_TYPE="${1:-auto}"  # shock, curiosity, contradiction, or auto (random)

if [ ! -f "$ANALYSIS_FILE" ]; then
    echo "❌ Error: $ANALYSIS_FILE not found"
    echo "   Run first: node analyze-web.js <URL>"
    exit 1
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ Error: GEMINI_API_KEY is not set"
    exit 1
fi

# Anti-stock filter - CRITICAL for visual novelty
ANTI_STOCK="ABSOLUTELY AVOID: generic stock photo aesthetics, typical influencer poses, shocked pretty girl trope, overused laptop-coffee setups, fake smiles, corporate handshakes, typical business meeting scenes, anything that looks like it came from Shutterstock."

# ═══════════════════════════════════════════════════════════════
# READ ANALYSIS DATA
# ═══════════════════════════════════════════════════════════════

PRODUCT_NAME=$(jq -r '.storytelling.productName // "product"' "$ANALYSIS_FILE")
NICHE=$(jq -r '.storytelling.niche // "business"' "$ANALYSIS_FILE")
UVP=$(jq -r '.storytelling.uvp // "The best solution"' "$ANALYSIS_FILE" | head -c 80)
HEADLINE=$(jq -r '.content.headline // ""' "$ANALYSIS_FILE")
TAGLINE=$(jq -r '.content.tagline // ""' "$ANALYSIS_FILE" | head -c 100)

# Features
FEATURE1=$(jq -r '.content.features[0].title // "Easy to use"' "$ANALYSIS_FILE")
FEATURE2=$(jq -r '.content.features[1].title // "Fast"' "$ANALYSIS_FILE")
FEATURE3=$(jq -r '.content.features[2].title // "Efficient"' "$ANALYSIS_FILE")

# Stats
STAT1=$(jq -r 'if .content.stats[0] then "\(.content.stats[0].value) \(.content.stats[0].label // "")" else "Thousands of users" end' "$ANALYSIS_FILE")

# Visual
COLOR_DESC=$(jq -r '.visualContext.colorDescription // "purple and blue gradient"' "$ANALYSIS_FILE")
FONT=$(jq -r '.visualContext.typography.headingFont // "bold sans-serif"' "$ANALYSIS_FILE")
IMAGE_THEME=$(jq -r '.visualContext.imageThemes[0] // "professional workspace"' "$ANALYSIS_FILE")
STYLE_GUIDE=$(jq -r '.visualContext.styleGuide // "Modern, clean aesthetic"' "$ANALYSIS_FILE")

# Hooks (use the first one)
HOOK=$(jq -r '.storytelling.hooks[0] // "Ready to change?"' "$ANALYSIS_FILE")

# CTA
CTA=$(jq -r '.content.ctas[0] // "Try it free"' "$ANALYSIS_FILE")

echo "═══════════════════════════════════════════════════════════════"
echo "🎨 GENERATING CAROUSEL: $PRODUCT_NAME"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📌 Visual theme: $IMAGE_THEME"
echo "📌 Colors: $COLOR_DESC"
echo "📌 Typography: $FONT"
echo "📌 Hook: $HOOK"
echo ""

# ═══════════════════════════════════════════════════════════════
# STRUCTURED PROMPT TEMPLATE (Nano Banana Pro best practices)
# Using explicit fields produces more consistent results
# ═══════════════════════════════════════════════════════════════

BASE_STYLE="Create an image of: TikTok vertical carousel slide (9:16 ratio, 768x1376 pixels). Style: professional social media content, cinematic, eye-catching, VISUALLY NOVEL. Composition: vertical portrait orientation, text centered at 28%% from top. Lighting: professional, depth of field, soft shadows. Background: $IMAGE_THEME. Color palette: $COLOR_DESC. Text overlay: large bold $FONT font in white with black outline for readability, 4-6 words per line, max 4 lines. $ANTI_STOCK. Avoid: text in bottom 20%% of image, blurry text, cut-off words, horizontal orientation, watermarks, logos."

# Initialize prompts tracking
echo '[]' > "$CAROUSEL_DIR/slide-prompts.json"

generate_slide() {
    local NUM=$1
    local TEXT=$2
    local SCENE=$3
    local INPUT_IMAGE=$4
    
    echo "📱 Slide $NUM: $TEXT"
    echo "   Scene: $SCENE"
    
    if [ -n "$INPUT_IMAGE" ] && [ -f "$INPUT_IMAGE" ]; then
        # Image-to-image: STRICT style matching - detect if reference is photo or illustration and match exactly
        PROMPT="CRITICAL: Look at the reference image style. If it's a REALISTIC PHOTO, generate a REALISTIC PHOTO. If it's an ILLUSTRATION/CARTOON, generate an ILLUSTRATION/CARTOON. NEVER mix styles. Match EXACTLY: the visual style (photo vs illustration), the artistic technique, color grading, lighting style, and overall aesthetic. Change ONLY: the text to \"$TEXT\" and the background scene to: $SCENE. Keep the SAME person/character style if applicable. Text must be large, bold, white with black outline, centered at 28%% from top. Avoid: text in bottom 20%%, blurry text, cut-off words, switching between photo and illustration styles."
        
        $UV_BIN run "$NANO_SCRIPT" \
            --prompt "$PROMPT" \
            --filename "$CAROUSEL_DIR/slide-$NUM.jpg" \
            --input-image "$INPUT_IMAGE" \
            --resolution 1K 2>/dev/null || echo "   ⚠️ Error on slide $NUM"
    else
        # First slide: establish the visual style
        PROMPT="$BASE_STYLE. The bold text says: \"$TEXT\". Scene description: $SCENE"
        
        $UV_BIN run "$NANO_SCRIPT" \
            --prompt "$PROMPT" \
            --filename "$CAROUSEL_DIR/slide-$NUM.jpg" \
            --resolution 1K 2>/dev/null || echo "   ⚠️ Error on slide $NUM"
    fi
    
    # Save prompt for analytics tracking
    local ESCAPED_PROMPT=$(echo "$PROMPT" | sed 's/"/\\"/g' | tr '\n' ' ')
    local ESCAPED_TEXT=$(echo "$TEXT" | sed 's/"/\\"/g' | tr '\n' ' ')
    local TMP_PROMPTS=$(cat "$CAROUSEL_DIR/slide-prompts.json")
    echo "$TMP_PROMPTS" | jq --arg slide "$NUM" --arg prompt "$ESCAPED_PROMPT" --arg text "$ESCAPED_TEXT" \
        '. += [{"slide": ($slide|tonumber), "text": $text, "prompt": $prompt}]' \
        > "$CAROUSEL_DIR/slide-prompts.json"
    echo ""
}

echo "═══════════════════════════════════════════════════════════════"
echo "📱 GENERATING 6 SLIDES WITH VISUAL COHERENCE"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ═══════════════════════════════════════════════════════════════
# GENERATE NICHE-SPECIFIC SLIDE CONTENT
# ═══════════════════════════════════════════════════════════════

# Default pain/agitation text (generic)
PAIN_TEXT="You're still doing everything manually... ⏰ HOURS wasted every week"
PAIN_SCENE="Same person, exhausted, clock showing time passing. Multiple tasks piling up."
AGIT_TEXT="Meanwhile, your competition is automating EVERYTHING 🚀"
AGIT_SCENE="Split screen: competitor succeeding vs you struggling. Growth charts going up for them."

# Override with niche-specific content
case "$NICHE" in
    social-media-tools)
        PAIN_TEXT="You upload to TikTok... then Instagram... then YouTube... ⏰ HOURS wasted"
        PAIN_SCENE="Same person, exhausted, clock showing time passing. Multiple app windows open."
        AGIT_TEXT="Meanwhile, your competition is posting on ALL platforms at once 🚀"
        AGIT_SCENE="Split screen: competitor succeeding vs you struggling. Growth charts going up for them."
        ;;
    developer-tools)
        PAIN_TEXT="Still writing boilerplate code for every integration? 💀"
        PAIN_SCENE="Developer frustrated, surrounded by error messages on multiple screens."
        AGIT_TEXT="Other devs are shipping 10x faster with the right tools 🚀"
        AGIT_SCENE="Split screen: fast developer vs slow developer. Clean code vs messy code."
        ;;
    ecommerce)
        PAIN_TEXT="Managing orders across 5 different platforms? 📦 That's exhausting"
        PAIN_SCENE="Person overwhelmed with packages, shipping labels, multiple browser tabs."
        AGIT_TEXT="Top sellers automated this months ago 🚀"
        AGIT_SCENE="Successful store owner relaxing while orders process automatically."
        ;;
    design)
        PAIN_TEXT="You know exactly what you want but can't afford a designer 😩"
        PAIN_SCENE="Person looking at beautiful rooms on phone, then looking at their plain room."
        AGIT_TEXT="Wait until you see what AI can do with just ONE photo 🤯"
        AGIT_SCENE="Before and after transformation of a room, dramatic improvement."
        ;;
    health)
        PAIN_TEXT="Tracking workouts on paper? Guessing your nutrition? 📝"
        PAIN_SCENE="Person confused with handwritten notes, old-school workout tracking."
        AGIT_TEXT="People who track properly see 3x better results 💪"
        AGIT_SCENE="Fit person confidently using tech vs person struggling with paper notes."
        ;;
    education)
        PAIN_TEXT="Still watching 3-hour lectures and remembering nothing? 😴"
        PAIN_SCENE="Student falling asleep at desk, surrounded by thick textbooks."
        AGIT_TEXT="Smart students are learning 10x faster with AI 🧠"
        AGIT_SCENE="Engaged student using modern tools, progress bars filling up."
        ;;
esac

# ═══════════════════════════════════════════════════════════════
# SLIDE 1: HOOK (establishes ALL visual style)
# Check if pre-generated hooks exist, otherwise generate with category
# ═══════════════════════════════════════════════════════════════

# Select hook type
if [ "$HOOK_TYPE" = "auto" ]; then
    # Random selection weighted by learnings (TODO: implement learning weights)
    HOOK_TYPES=("shock" "curiosity" "contradiction")
    HOOK_TYPE="${HOOK_TYPES[$RANDOM % 3]}"
    echo "🎲 Auto-selected hook type: $HOOK_TYPE"
fi

# Check for pre-generated hook
PRE_HOOK="$HOOKS_DIR/hook-${HOOK_TYPE}.jpg"
if [ -f "$PRE_HOOK" ]; then
    echo "📎 Using pre-generated $HOOK_TYPE hook"
    cp "$PRE_HOOK" "$CAROUSEL_DIR/slide-1.jpg"
    # Get hook text from metadata
    if [ -f "$HOOKS_DIR/hooks-meta.json" ]; then
        HOOK=$(jq -r ".hooks[] | select(.type==\"$HOOK_TYPE\") | .text" "$HOOKS_DIR/hooks-meta.json")
    fi
else
    echo "🎨 Generating $HOOK_TYPE hook on-the-fly"
    
    # Generate hook based on type with anti-stock and visual novelty
    case "$HOOK_TYPE" in
        shock)
            HOOK_SCENE="Surreal, impossible scene that stops the scroll. Something visually WRONG or ABSURD. Chaotic but eye-catching. Related to $NICHE but exaggerated to the extreme."
            ;;
        curiosity)
            HOOK_SCENE="Mysterious, intriguing scene that creates information gap. Something being revealed, secrets, dramatic lighting. Makes viewer NEED to see more."
            ;;
        contradiction)
            HOOK_SCENE="Visual contradiction - two things that shouldn't exist together. Relaxed person with intense activity. Impossible combination that makes viewer think 'wait, how?'"
            ;;
        *)
            HOOK_SCENE="Frustrated person at desk, overwhelmed, chaotic environment. Stressed expression. Related to $NICHE."
            ;;
    esac
    
    generate_slide 1 "$HOOK" "$HOOK_SCENE"
fi

# Save hook info for tracking/learning (including image prompt for analytics)
# Escape HOOK_SCENE for JSON
HOOK_SCENE_ESCAPED=$(echo "$HOOK_SCENE" | sed 's/"/\\"/g' | tr '\n' ' ')
cat > "$CAROUSEL_DIR/hook-info.json" << EOF
{
  "hook_type": "$HOOK_TYPE",
  "hook_text": "$HOOK",
  "image_prompt": "$HOOK_SCENE_ESCAPED",
  "visual_style": "$IMAGE_THEME",
  "colors": "$COLOR_DESC",
  "generated_at": "$(date -Iseconds)"
}
EOF

# Reference for coherence
REF="$CAROUSEL_DIR/slide-1.jpg"

# SLIDE 2: PROBLEM/PAIN
generate_slide 2 "$PAIN_TEXT" "$PAIN_SCENE" "$REF"

# SLIDE 3: AGITATION (competition)
generate_slide 3 "$AGIT_TEXT" "$AGIT_SCENE" "$REF"

# SLIDE 4: SOLUTION (introduce product)
SOLUTION_TEXT="${PRODUCT_NAME^^}: $TAGLINE"
generate_slide 4 "$SOLUTION_TEXT" "Triumphant moment, relief, solution revealed. Clean interface, simple. One click = everywhere." "$REF"

# SLIDE 5: KEY FEATURE
generate_slide 5 "✓ $FEATURE1" "Clean, professional, benefit-focused. Happy user, productivity boost." "$REF"

# SLIDE 6: CTA
CTA_TEXT="Link in bio 👆 $CTA"
generate_slide 6 "$CTA_TEXT" "Strong call to action, arrow pointing up, urgency, invitation to try." "$REF"

echo "═══════════════════════════════════════════════════════════════"
echo "✅ SLIDES GENERATED"
echo "═══════════════════════════════════════════════════════════════"
echo ""
ls -la "$CAROUSEL_DIR"/*.jpg 2>/dev/null
echo ""

# ═══════════════════════════════════════════════════════════════
# GENERATE OPTIMIZED CAPTION
# ═══════════════════════════════════════════════════════════════

CAPTION="$HOOK

$PAIN_TEXT

The solution: $PRODUCT_NAME ✨
$TAGLINE

✓ $FEATURE1
✓ $FEATURE2

$STAT1 already using it 🔥

👉 Link in bio to try it FREE

#${PRODUCT_NAME//[^a-zA-Z0-9]/} #socialmedia #marketing #contentcreator #viral #fyp #productivity"

echo "📝 SUGGESTED CAPTION:"
echo "───────────────────────────────────────────────────────────────"
echo "$CAPTION"
echo "───────────────────────────────────────────────────────────────"
echo ""
echo "$CAPTION" > "$CAROUSEL_DIR/caption.txt"
echo "💾 Saved to: $CAROUSEL_DIR/caption.txt"
echo "💾 Prompts saved to: $CAROUSEL_DIR/slide-prompts.json"
