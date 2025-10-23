#!/bin/bash
# Overnight Plugin Enhancement System - Using gcloud CLI
# Analyzes plugins against Anthropic standards and enhances them using Vertex AI Gemini

set -e

# Configuration
PROJECT_ID="ccpi-web-app-prod"
LOCATION="us-central1"
MODEL="gemini-2.0-flash-exp"
RATE_LIMIT_DELAY=90
BACKUP_DIR="backups/plugin-enhancements"
PLUGINS_DIR="plugins"
STANDARDS_DOC="claudes-docs/anthropic-agent-skills-complete-reference.md"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Initialize
echo -e "${BLUE}🤖 Overnight Plugin Enhancement System (gcloud)${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check gcloud auth
echo -n "Checking gcloud authentication... "
if gcloud auth application-default print-access-token &>/dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo ""
    echo "Please authenticate:"
    echo "  gcloud auth application-default login"
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Load standards document
if [ ! -f "$STANDARDS_DOC" ]; then
    echo -e "${RED}✗ Standards document not found: $STANDARDS_DOC${NC}"
    exit 1
fi

STANDARDS=$(cat "$STANDARDS_DOC")
echo -e "${GREEN}✓${NC} Loaded Anthropic standards ($(wc -c < "$STANDARDS_DOC") bytes)"
echo ""

# Function to call Gemini via REST API with gcloud auth
call_gemini() {
    local prompt="$1"
    local temperature="${2:-0.3}"

    # Get access token
    local access_token=$(gcloud auth application-default print-access-token)

    # Escape prompt for JSON
    local escaped_prompt=$(echo "$prompt" | jq -Rs .)

    # Create JSON payload
    local payload=$(cat <<EOF
{
  "contents": [{
    "role": "user",
    "parts": [{"text": $escaped_prompt}]
  }],
  "generationConfig": {
    "temperature": $temperature,
    "maxOutputTokens": 8192,
    "topP": 0.95,
    "topK": 40
  }
}
EOF
)

    # Call Vertex AI REST API
    local response=$(curl -s -X POST \
        "https://${LOCATION}-aiplatform.googleapis.com/v1/projects/${PROJECT_ID}/locations/${LOCATION}/publishers/google/models/${MODEL}:generateContent" \
        -H "Authorization: Bearer ${access_token}" \
        -H "Content-Type: application/json" \
        -d "$payload")

    # Extract text from response
    echo "$response" | jq -r '.candidates[0].content.parts[0].text' 2>/dev/null || echo "$response"
}

# Function to enhance a single plugin
enhance_plugin() {
    local plugin_path="$1"
    local plugin_name=$(basename "$plugin_path")

    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🔧 Processing: $plugin_name${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    # Check if plugin has required files
    if [ ! -f "$plugin_path/.claude-plugin/plugin.json" ]; then
        echo -e "${YELLOW}⚠️  No plugin.json found, skipping${NC}"
        return
    fi

    # Read plugin metadata
    local plugin_json=$(cat "$plugin_path/.claude-plugin/plugin.json")
    local readme=""
    [ -f "$plugin_path/README.md" ] && readme=$(cat "$plugin_path/README.md")

    # Check if SKILL.md already exists
    local skill_path="$plugin_path/skills/skill-adapter/SKILL.md"
    local has_skill="false"
    [ -f "$skill_path" ] && has_skill="true"

    echo ""
    echo -e "${YELLOW}📊 Step 1: Analyzing plugin structure...${NC}"

    # Create analysis prompt
    local analysis_prompt="You are an expert at analyzing Claude Code plugins against Anthropic's Agent Skills standards.

# ANTHROPIC STANDARDS
${STANDARDS:0:15000}

# PLUGIN TO ANALYZE
Name: $plugin_name
Path: $plugin_path
Has existing SKILL.md: $has_skill

## plugin.json
$plugin_json

## README.md
${readme:0:10000}

# YOUR TASK
Analyze this plugin and return ONLY valid JSON with this structure:
{
  \"quality_score\": 0-100,
  \"has_skill_md\": true/false,
  \"skill_md_size_bytes\": 0,
  \"gaps\": [\"gap1\", \"gap2\"],
  \"recommended_actions\": [\"action1\", \"action2\"]
}

Return ONLY the JSON, no other text."

    echo "  Calling Gemini API..."
    local analysis=$(call_gemini "$analysis_prompt" "0.3")

    # Rate limiting
    echo -e "  ${YELLOW}⏸️  Rate limiting: ${RATE_LIMIT_DELAY}s...${NC}"
    sleep $RATE_LIMIT_DELAY

    echo "$analysis"
    echo ""

    # Check if we should create/enhance SKILL.md
    local quality_score=$(echo "$analysis" | jq -r '.quality_score' 2>/dev/null || echo "0")

    if [ "$quality_score" -lt 80 ]; then
        echo -e "${YELLOW}📝 Step 2: Generating enhanced SKILL.md...${NC}"

        # Create enhancement prompt
        local skill_prompt="You are an expert at creating Claude Code Agent Skills following Anthropic's standards.

# ANTHROPIC STANDARDS (Your Bible)
${STANDARDS:0:15000}

# PLUGIN CONTEXT
Name: $plugin_name

## plugin.json
$plugin_json

## README.md (excerpt)
${readme:0:10000}

# YOUR TASK
Create a comprehensive SKILL.md file following these requirements:

1. YAML frontmatter with hyphen-case name
2. Multi-line description with trigger phrases
3. 8,000+ bytes of content
4. Imperative/infinitive writing style (not \"you should\")
5. 4-6 workflow phases with detailed steps
6. 10-15 code examples
7. References to bundled resources (scripts/, references/, assets/)
8. Progressive disclosure model

Return ONLY the complete SKILL.md content, no other text."

        echo "  Calling Gemini API..."
        local skill_content=$(call_gemini "$skill_prompt" "0.4")

        # Rate limiting
        echo -e "  ${YELLOW}⏸️  Rate limiting: ${RATE_LIMIT_DELAY}s...${NC}"
        sleep $RATE_LIMIT_DELAY

        # Create backup
        if [ -f "$skill_path" ]; then
            local backup_path="$BACKUP_DIR/$(date +%Y%m%d_%H%M%S)_${plugin_name}_SKILL.md.bak"
            mkdir -p "$(dirname "$backup_path")"
            cp "$skill_path" "$backup_path"
            echo -e "${GREEN}✓${NC} Backed up existing SKILL.md"
        fi

        # Write new SKILL.md
        mkdir -p "$(dirname "$skill_path")"
        echo "$skill_content" > "$skill_path"

        local new_size=$(wc -c < "$skill_path")
        echo -e "${GREEN}✓${NC} Created SKILL.md ($new_size bytes)"

        # Create bundled resource directories
        mkdir -p "$plugin_path/skills/skill-adapter/scripts"
        mkdir -p "$plugin_path/skills/skill-adapter/references"
        mkdir -p "$plugin_path/skills/skill-adapter/assets"

        echo "# Scripts for $plugin_name" > "$plugin_path/skills/skill-adapter/scripts/README.md"
        echo "# References for $plugin_name" > "$plugin_path/skills/skill-adapter/references/README.md"
        echo "# Assets for $plugin_name" > "$plugin_path/skills/skill-adapter/assets/README.md"

        echo -e "${GREEN}✓${NC} Created bundled resource directories"

        echo ""
        echo -e "${GREEN}🎉 Enhancement complete!${NC}"
        echo "  Quality score: $quality_score → ~85 (estimated)"
        echo "  SKILL.md size: $new_size bytes"
    else
        echo -e "${GREEN}✓${NC} Plugin already meets quality standards (score: $quality_score)"
    fi
}

# Main execution
if [ "$1" == "--plugin" ]; then
    # Single plugin mode
    PLUGIN_NAME="$2"

    # Find plugin
    PLUGIN_PATH=$(find plugins -type d -name "$PLUGIN_NAME" | head -1)

    if [ -z "$PLUGIN_PATH" ]; then
        echo -e "${RED}✗ Plugin not found: $PLUGIN_NAME${NC}"
        exit 1
    fi

    enhance_plugin "$PLUGIN_PATH"

elif [ "$1" == "--limit" ]; then
    # Limited batch mode
    LIMIT="$2"
    echo "Processing first $LIMIT plugins..."

    count=0
    for category in productivity security testing packages examples community mcp; do
        if [ -d "plugins/$category" ]; then
            for plugin_dir in plugins/$category/*/; do
                if [ $count -ge $LIMIT ]; then
                    break 2
                fi
                enhance_plugin "$plugin_dir"
                ((count++))
            done
        fi
    done

else
    # Full batch mode - all plugins
    echo "Processing ALL plugins..."

    total=0
    for category in productivity security testing packages examples community mcp; do
        if [ -d "plugins/$category" ]; then
            for plugin_dir in plugins/$category/*/; do
                enhance_plugin "$plugin_dir"
                ((total++))
            done
        fi
    done

    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ Batch enhancement complete!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo "  Total plugins processed: $total"
fi

echo ""
