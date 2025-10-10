#!/bin/bash
# Tests plugin installation in isolated environment
# Usage: ./test-installation.sh <plugin-directory>

set -e

PLUGIN_DIR="${1:-plugins/devops/git-commit-smart}"
TEST_DIR="/tmp/claude-plugin-test-$$"
START_TIME=$(date +%s)

echo "🧪 Testing plugin installation..."
echo "Plugin: $PLUGIN_DIR"
echo "Test directory: $TEST_DIR"
echo ""

# 1. Create test environment
echo "📦 Creating test environment..."
mkdir -p "$TEST_DIR/.claude-plugins"

# 2. Copy plugin
echo "📋 Copying plugin files..."
cp -r "$PLUGIN_DIR" "$TEST_DIR/.claude-plugins/"
PLUGIN_NAME=$(basename "$PLUGIN_DIR")

# 3. Verify structure
echo "🔍 Verifying plugin structure..."
if [[ ! -f "$TEST_DIR/.claude-plugins/$PLUGIN_NAME/.claude-plugin/plugin.json" ]]; then
  echo "❌ Missing plugin.json"
  exit 1
fi

# 4. Count plugin files
COMMAND_COUNT=$(find "$TEST_DIR/.claude-plugins/$PLUGIN_NAME/commands" -name "*.md" 2>/dev/null | wc -l)
AGENT_COUNT=$(find "$TEST_DIR/.claude-plugins/$PLUGIN_NAME/agents" -name "*.md" 2>/dev/null | wc -l)
echo "✅ Found $COMMAND_COUNT command(s) and $AGENT_COUNT agent(s)"

# 5. Verify all plugins have valid frontmatter
echo "🔬 Verifying plugin frontmatter..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
find "$TEST_DIR/.claude-plugins/$PLUGIN_NAME" -name "*.md" -path "*/commands/*" -o -path "*/agents/*" 2>/dev/null | while read -r md_file; do
  if [[ -f "$md_file" ]]; then
    if ! python3 "$SCRIPT_DIR/check-frontmatter.py" "$md_file" > /dev/null 2>&1; then
      echo "❌ Invalid frontmatter: $md_file"
      exit 1
    fi
  fi
done

# 6. Check plugin.json
echo "📝 Validating plugin.json..."
PLUGIN_JSON="$TEST_DIR/.claude-plugins/$PLUGIN_NAME/.claude-plugin/plugin.json"
if ! jq empty "$PLUGIN_JSON" 2>/dev/null; then
  echo "❌ Invalid plugin.json"
  exit 1
fi

# 7. Verify required fields
for field in name version description author; do
  if ! jq -e ".$field" "$PLUGIN_JSON" > /dev/null 2>&1; then
    echo "❌ Missing required field: $field"
    exit 1
  fi
done

# 8. Cleanup
echo "🧹 Cleaning up test environment..."
rm -rf "$TEST_DIR"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ INSTALLATION TEST PASSED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Plugin: $PLUGIN_NAME"
echo "Commands: $COMMAND_COUNT"
echo "Agents: $AGENT_COUNT"
echo "Duration: ${DURATION}s"
echo ""

if [ "$DURATION" -gt 60 ]; then
  echo "⚠️  Warning: Installation took longer than 1 minute"
  exit 1
fi

exit 0
