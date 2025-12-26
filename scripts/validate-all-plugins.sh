#!/bin/bash
# Validates all plugins before allowing deployment
# Run this after creating each plugin to ensure quality

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
ERRORS=0
WARNINGS=0

# Note: With 'set -e', we need to handle arithmetic carefully
# ((VAR++)) returns 0 (false/error) when VAR is 0, which would exit the script
# Use ERRORS=$((ERRORS + 1)) instead

echo "🔍 Running comprehensive validation..."
echo ""

# Get target directory (default to all plugins)
TARGET_DIR="${1:-plugins}"

# 1. JSON Schema Validation
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📄 Validating JSON files..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

while IFS= read -r json_file; do
  echo "  Checking: $json_file"

  # Check if jq can parse it
  if ! jq empty "$json_file" 2>/dev/null; then
    echo -e "${RED}❌ Invalid JSON: $json_file${NC}"
    ERRORS=$((ERRORS + 1))
    continue
  fi

  # Validate plugin.json against schema if applicable
  if [[ "$json_file" == */plugin.json ]]; then
    # Check for required fields
    if ! jq -e '.name' "$json_file" >/dev/null 2>&1; then
      echo -e "${RED}❌ Missing 'name' field: $json_file${NC}"
      ERRORS=$((ERRORS + 1))
    fi
    if ! jq -e '.version' "$json_file" >/dev/null 2>&1; then
      echo -e "${RED}❌ Missing 'version' field: $json_file${NC}"
      ERRORS=$((ERRORS + 1))
    fi
    if ! jq -e '.description' "$json_file" >/dev/null 2>&1; then
      echo -e "${RED}❌ Missing 'description' field: $json_file${NC}"
      ERRORS=$((ERRORS + 1))
    fi
    if ! jq -e '.author' "$json_file" >/dev/null 2>&1; then
      echo -e "${RED}❌ Missing 'author' field: $json_file${NC}"
      ERRORS=$((ERRORS + 1))
    fi

    # NEW: Check for invalid/forbidden fields (Claude Code strict schema)
    # Allowed fields: name, version, description, author, repository, homepage, license, keywords
    INVALID_FIELDS=$(jq -r 'keys - ["name","version","description","author","repository","homepage","license","keywords"] | .[]' "$json_file" 2>/dev/null)

    if [ -n "$INVALID_FIELDS" ]; then
      echo -e "${RED}❌ Invalid fields in $json_file:${NC}"
      echo "$INVALID_FIELDS" | while read -r field; do
        echo -e "   ${YELLOW}Unrecognized key: '$field' (Claude Code doesn't support this field)${NC}"
      done
      ERRORS=$((ERRORS + 1))
    fi
  fi

  # Validate hooks.json structure
  if [[ "$json_file" == */hooks.json ]]; then
    if ! jq -e '.hooks' "$json_file" >/dev/null 2>&1; then
      echo -e "${YELLOW}⚠️  Warning: hooks.json missing 'hooks' object: $json_file${NC}"
      WARNINGS=$((WARNINGS + 1))
    fi
  fi

done < <(find "$TARGET_DIR" -name "*.json" -type f 2>/dev/null)

if [ "$ERRORS" -eq 0 ]; then
  echo -e "${GREEN}✅ All JSON valid${NC}"
else
  echo -e "${RED}❌ Found $ERRORS JSON errors${NC}"
fi
echo ""

# 2. Markdown Frontmatter Validation
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Validating markdown frontmatter..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if frontmatter validation script is available
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
HAS_PYTHON3=false
HAS_FRONTMATTER_SCRIPT=false

if command -v python3 &> /dev/null; then
  HAS_PYTHON3=true
  if [[ -f "$SCRIPT_DIR/validate-frontmatter.py" ]]; then
    HAS_FRONTMATTER_SCRIPT=true
  else
    echo -e "${RED}❌ validate-frontmatter.py not found - frontmatter validation FAILED${NC}"
    ERRORS=$((ERRORS + 1))
  fi
else
  echo -e "${RED}❌ Python3 not found - frontmatter validation FAILED${NC}"
  ERRORS=$((ERRORS + 1))
fi

while IFS= read -r md_file; do
  echo "  Checking: $md_file"

  # Check if file has frontmatter
  if ! grep -q "^---" "$md_file"; then
    echo -e "${RED}❌ No frontmatter found: $md_file${NC}"
    ERRORS=$((ERRORS + 1))
    continue
  fi

  # Validate with Python script if available
  if [[ "$HAS_FRONTMATTER_SCRIPT" == "true" ]]; then
    if ! python3 "$SCRIPT_DIR/validate-frontmatter.py" "$md_file" 2>&1; then
      ERRORS=$((ERRORS + 1))
    fi
  fi

done < <(find "$TARGET_DIR" \( -path "*/commands/*.md" -o -path "*/agents/*.md" \) 2>/dev/null | grep -v "/packages/" | head -100)

echo ""

# 3. Duplicate Shortcut Detection
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔑 Checking for duplicate shortcuts..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Exclude plugins/packages/ (nested plugin packs) and SHORTCUT_PLACEHOLDER values
shortcuts=$(find "$TARGET_DIR" -name "*.md" 2>/dev/null | grep -v "/packages/" | xargs grep -h "^shortcut:" 2>/dev/null | awk '{print $2}' | grep -v "SHORTCUT_PLACEHOLDER" | sort)
duplicates=$(echo "$shortcuts" | uniq -d)

if [[ -n "$duplicates" ]]; then
  echo -e "${YELLOW}⚠️  Duplicate shortcuts found (non-blocking):${NC}"
  echo "$duplicates" | while read -r dup; do
    echo "  - '$dup'"
    # Show which files have this shortcut
    grep -r "^shortcut: $dup" "$TARGET_DIR" --include="*.md" 2>/dev/null | grep -v "/packages/" | head -3
  done
  WARNINGS=$((WARNINGS + 1))
else
  echo -e "${GREEN}✅ No duplicate shortcuts${NC}"
fi
echo ""

# 4. File Reference Validation
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📂 Validating file references..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

while IFS= read -r plugin_json; do
  plugin_dir=$(dirname "$(dirname "$plugin_json")")

  echo "  Checking references in: $plugin_json"

  # Check commands path exists if specified
  if jq -e '.commands' "$plugin_json" > /dev/null 2>&1; then
    commands_path=$(jq -r '.commands' "$plugin_json")
    # Handle glob patterns
    if [[ "$commands_path" != *"*"* ]]; then
      full_path="$plugin_dir/$commands_path"
      if [[ ! -d "$full_path" && ! -f "$full_path" ]]; then
        echo -e "${RED}❌ Commands path doesn't exist: $full_path${NC}"
        ERRORS=$((ERRORS + 1))
      fi
    fi
  fi

  # Check agents path exists if specified
  if jq -e '.agents' "$plugin_json" > /dev/null 2>&1; then
    agents_path=$(jq -r '.agents' "$plugin_json")
    if [[ "$agents_path" != *"*"* ]]; then
      full_path="$plugin_dir/$agents_path"
      if [[ ! -d "$full_path" && ! -f "$full_path" ]]; then
        echo -e "${RED}❌ Agents path doesn't exist: $full_path${NC}"
        ERRORS=$((ERRORS + 1))
      fi
    fi
  fi

done < <(find "$TARGET_DIR" -name "plugin.json" 2>/dev/null)

if [ "$ERRORS" -eq 0 ]; then
  echo -e "${GREEN}✅ All file references valid${NC}"
fi
echo ""

# 5. Script Executability
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 Checking script permissions..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

while IFS= read -r script; do
  if [[ ! -x "$script" ]]; then
    echo -e "${RED}❌ Script not executable: $script${NC}"
    echo "   Run: chmod +x $script"
    ERRORS=$((ERRORS + 1))
  fi
done < <(find "$TARGET_DIR" -name "*.sh" 2>/dev/null)

if [ "$ERRORS" -eq 0 ]; then
  echo -e "${GREEN}✅ All scripts executable${NC}"
fi
echo ""

# 6. Required Documentation Check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 Checking required documentation..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check each plugin for README.md
for plugin_dir in plugins/*/*/; do
  # Skip if not a directory
  if [[ ! -d "$plugin_dir" ]]; then
    continue
  fi

  # Only check if it has a .claude-plugin directory (indicates it's a plugin)
  if [[ ! -d "$plugin_dir/.claude-plugin" ]]; then
    continue
  fi

  echo "  Checking: $plugin_dir"

  if [[ ! -f "$plugin_dir/README.md" ]]; then
    echo -e "${YELLOW}⚠️  Missing README.md: $plugin_dir${NC}"
    WARNINGS=$((WARNINGS + 1))
  fi
done

echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 VALIDATION SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ "$ERRORS" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
  echo -e "${GREEN}✅ All validation checks passed!${NC}"
  echo -e "${GREEN}Safe to commit and deploy.${NC}"
  exit 0
elif [ "$ERRORS" -eq 0 ]; then
  echo -e "${YELLOW}⚠️  Validation passed with $WARNINGS warning(s)${NC}"
  echo "Review warnings above before proceeding."
  exit 0
else
  echo -e "${RED}❌ Validation failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
  echo "Fix errors above before proceeding."
  exit 1
fi
