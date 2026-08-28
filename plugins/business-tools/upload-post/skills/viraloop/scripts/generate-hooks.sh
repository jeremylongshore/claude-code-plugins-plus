#!/bin/bash
# Generate multiple hook variants for A/B testing
# NOW WITH LEARNING: reads learnings.json and adapts hooks based on what works
set -e

CAROUSEL_DIR="/tmp/carousel"
ANALYSIS_FILE="$CAROUSEL_DIR/analysis.json"
UV_BIN="${HOME}/.local/bin/uv"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
NANO_SCRIPT="$SCRIPT_DIR/generate_image.py"
HOOKS_DIR="$CAROUSEL_DIR/hooks"
LEARNINGS_FILE="$SKILL_DIR/learnings.json"

mkdir -p "$HOOKS_DIR"

if [ ! -f "$ANALYSIS_FILE" ]; then
    echo "❌ Error: $ANALYSIS_FILE not found"
    exit 1
fi

if [ -z "$GEMINI_API_KEY" ]; then
    echo "❌ Error: GEMINI_API_KEY is not set"
    exit 1
fi

# Read analysis data
PRODUCT_NAME=$(jq -r '.storytelling.productName // "product"' "$ANALYSIS_FILE")
NICHE=$(jq -r '.storytelling.niche // "business"' "$ANALYSIS_FILE")
COLOR_DESC=$(jq -r '.visualContext.colorDescription // "purple and blue gradient"' "$ANALYSIS_FILE")
FONT=$(jq -r '.visualContext.typography.headingFont // "bold sans-serif"' "$ANALYSIS_FILE")
LANGUAGE="${VIRALOOP_LANG:-es}"

# ═══════════════════════════════════════════════════════════════
# LOAD LEARNINGS (if available)
# ═══════════════════════════════════════════════════════════════
PROMPT_BOOST=""
PREFER_TYPE=""
USE_WORDS=""
USE_EMOJIS=""
AVOID_WORDS=""

if [ -f "$LEARNINGS_FILE" ]; then
    echo "🧠 Loading learnings from previous posts..."
    PROMPT_BOOST=$(jq -r '.recommendations.promptBoost // ""' "$LEARNINGS_FILE")
    PREFER_TYPE=$(jq -r '.recommendations.preferHookType // ""' "$LEARNINGS_FILE")
    USE_WORDS=$(jq -r '.recommendations.useWords | join(", ")' "$LEARNINGS_FILE" 2>/dev/null || echo "")
    USE_EMOJIS=$(jq -r '.recommendations.useEmojis | join(" ")' "$LEARNINGS_FILE" 2>/dev/null || echo "")
    AVOID_WORDS=$(jq -r '.recommendations.avoidWords | join(", ")' "$LEARNINGS_FILE" 2>/dev/null || echo "")
    
    if [ -n "$PROMPT_BOOST" ]; then
        echo "   ✅ Found learnings:"
        echo "      Prefer type: $PREFER_TYPE"
        [ -n "$USE_WORDS" ] && echo "      Use words: $USE_WORDS"
        [ -n "$USE_EMOJIS" ] && echo "      Use emojis: $USE_EMOJIS"
        [ -n "$AVOID_WORDS" ] && echo "      Avoid words: $AVOID_WORDS"
        echo ""
    fi
else
    echo "📝 No learnings yet - will learn after first analytics check"
    echo ""
fi

# Anti-stock filter
ANTI_STOCK="ABSOLUTELY AVOID: generic stock photo aesthetics, typical influencer poses, shocked pretty girl trope, overused laptop-coffee setups, fake smiles, corporate handshakes, typical business meeting scenes. Create something UNEXPECTED and WEIRD that stops the scroll."

echo "═══════════════════════════════════════════════════════════════"
echo "🎣 GENERATING 3 HOOK VARIANTS: $PRODUCT_NAME"
echo "   Language: $LANGUAGE | Niche: $NICHE"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ═══════════════════════════════════════════════════════════════
# BUILD LEARNING-ENHANCED PROMPT
# ═══════════════════════════════════════════════════════════════
LEARNING_CONTEXT=""
if [ -n "$PROMPT_BOOST" ]; then
    LEARNING_CONTEXT="

IMPORTANT - DATA FROM PREVIOUS POSTS:
$PROMPT_BOOST

Apply these learnings to make the hook more effective. The data shows what actually works with this audience."
fi

# ═══════════════════════════════════════════════════════════════
# GENERATE HOOKS USING GEMINI (dynamic, not hardcoded)
# ═══════════════════════════════════════════════════════════════

generate_hook_text() {
    local HOOK_TYPE=$1
    local HOOK_STYLE=$2
    
    # Use Gemini to generate contextual hook text
    local PROMPT="Generate ONE short TikTok hook text (max 8 words) in ${LANGUAGE^^} for a $NICHE product called '$PRODUCT_NAME'.

Hook type: $HOOK_TYPE
Style: $HOOK_STYLE

Requirements:
- Must be in ${LANGUAGE^^} (Spanish if es, English if en)
- Max 8 words + 1-2 emojis
- Must create immediate curiosity or shock
- Must feel native to TikTok (not corporate)
${LEARNING_CONTEXT}

Examples of $HOOK_TYPE hooks:
- SHOCK: '3 HORAS al día publicando = contenido MUERTO 💀'
- CURIOSITY: '¿Por qué los TOP publican 10x más rápido? 🤔'
- CONTRADICTION: 'Menos esfuerzo = MÁS alcance 📈'

Return ONLY the hook text, nothing else."

    # Call Gemini API
    local RESPONSE=$(curl -s "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=$GEMINI_API_KEY" \
        -H 'Content-Type: application/json' \
        -d "{
            \"contents\": [{\"parts\":[{\"text\": $(echo "$PROMPT" | jq -Rs .)}]}],
            \"generationConfig\": {\"temperature\": 0.9, \"maxOutputTokens\": 50}
        }" 2>/dev/null)
    
    echo "$RESPONSE" | jq -r '.candidates[0].content.parts[0].text // ""' | tr -d '\n' | head -c 100
}

generate_scene_prompt() {
    local HOOK_TYPE=$1
    local HOOK_TEXT=$2
    
    case "$HOOK_TYPE" in
        shock)
            echo "Surreal scene showing overwhelming chaos related to: $HOOK_TEXT. Person drowning in screens/tasks, everything on fire but they're smiling nervously. Nightmarish but eye-catching. Multiple clones doing same task."
            ;;
        curiosity)
            echo "Mysterious scene related to: $HOOK_TEXT. Split view: exhausted person on one side, relaxed successful person on other with mysterious glow. Question marks, intriguing shadows, secret being revealed."
            ;;
        contradiction)
            echo "Contradiction scene for: $HOOK_TEXT. Person completely relaxed (beach/hammock) while intense work happens automatically in background. Ultimate lifestyle contradiction - chill person + massive productivity."
            ;;
    esac
}

# ═══════════════════════════════════════════════════════════════
# GENERATE ALL 3 HOOK TYPES
# ═══════════════════════════════════════════════════════════════

for HOOK_TYPE in shock curiosity contradiction; do
    case "$HOOK_TYPE" in
        shock)
            EMOJI="🔴"
            STYLE="Create fear/urgency. Show what happens if they DON'T act. Use words like: error, muerto, pierdes, problema."
            ;;
        curiosity)
            EMOJI="🟡"
            STYLE="Create information gap. Ask a question they NEED answered. Use: ¿por qué?, ¿cómo?, secreto, truco."
            ;;
        contradiction)
            EMOJI="🟢"
            STYLE="Show impossible contrast. Something that shouldn't work together. Use: menos=más, sin esfuerzo, automático."
            ;;
    esac
    
    echo "$EMOJI Generating $HOOK_TYPE hook..."
    
    # Generate hook text with AI
    HOOK_TEXT=$(generate_hook_text "$HOOK_TYPE" "$STYLE")
    
    if [ -z "$HOOK_TEXT" ]; then
        # Fallback if API fails
        case "$HOOK_TYPE" in
            shock) HOOK_TEXT="Tu contenido está MURIENDO 💀" ;;
            curiosity) HOOK_TEXT="¿Por qué ellos crecen y tú no? 🤔" ;;
            contradiction) HOOK_TEXT="Publico menos, crezco más 🤷" ;;
        esac
    fi
    
    echo "   Text: $HOOK_TEXT"
    
    # Generate scene description
    SCENE=$(generate_scene_prompt "$HOOK_TYPE" "$HOOK_TEXT")
    
    # Build image prompt
    PROMPT="TikTok vertical slide (9:16, 768x1376). ${HOOK_TYPE^^} HOOK - must stop the scroll immediately. $ANTI_STOCK. Scene: $SCENE. Style: dramatic, cinematic, slightly surreal but not too abstract. Color palette: $COLOR_DESC. Text overlay: \"$HOOK_TEXT\" in large bold $FONT, white with black outline, positioned at 28% from top. The visual should feel IMPOSSIBLE or ABSURD."
    
    # Generate image
    $UV_BIN run "$NANO_SCRIPT" \
        --prompt "$PROMPT" \
        --filename "$HOOKS_DIR/hook-${HOOK_TYPE}.jpg" \
        --resolution 1K 2>/dev/null || echo "   ⚠️ Error generating $HOOK_TYPE hook image"
    
    # Save individual hook metadata
    echo "{\"type\": \"$HOOK_TYPE\", \"text\": \"$HOOK_TEXT\", \"scene\": \"$SCENE\"}" > "$HOOKS_DIR/hook-${HOOK_TYPE}.json"
    
    echo ""
done

echo "═══════════════════════════════════════════════════════════════"
echo "✅ 3 HOOK VARIANTS GENERATED"
echo "═══════════════════════════════════════════════════════════════"
ls -la "$HOOKS_DIR"/*.jpg 2>/dev/null
echo ""

# Save combined hook metadata
cat > "$HOOKS_DIR/hooks-meta.json" << EOF
{
  "generated_at": "$(date -Iseconds)",
  "product": "$PRODUCT_NAME",
  "niche": "$NICHE",
  "language": "$LANGUAGE",
  "learnings_applied": $([ -n "$PROMPT_BOOST" ] && echo "true" || echo "false"),
  "preferred_type": "$PREFER_TYPE",
  "hooks": [
    $(cat "$HOOKS_DIR/hook-shock.json" 2>/dev/null || echo '{"type":"shock","text":"","scene":""}'),
    $(cat "$HOOKS_DIR/hook-curiosity.json" 2>/dev/null || echo '{"type":"curiosity","text":"","scene":""}'),
    $(cat "$HOOKS_DIR/hook-contradiction.json" 2>/dev/null || echo '{"type":"contradiction","text":"","scene":""}')
  ]
}
EOF

echo "📋 Hook metadata saved to: $HOOKS_DIR/hooks-meta.json"
echo ""
if [ -n "$PREFER_TYPE" ]; then
    echo "💡 TIP: Based on learnings, $PREFER_TYPE hooks perform best. Consider using --hook-type $PREFER_TYPE"
fi
echo ""
echo "👉 Next: Review hooks and select best one, then run generate-slides.sh with --hook-type [shock|curiosity|contradiction]"
